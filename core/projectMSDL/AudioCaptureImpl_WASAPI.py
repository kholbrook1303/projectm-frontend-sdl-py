import logging
import threading
import time

import numpy as np

from ctypes import Structure, POINTER, cast, c_void_p, c_uint32, c_ulong, c_uint64, string_at
from ctypes.wintypes import DWORD, WORD
from comtypes import CLSCTX_ALL, GUID, COMMETHOD, HRESULT, IUnknown
from comtypes import CoInitializeEx, CoUninitialize, COINIT_MULTITHREADED
from pycaw.api.audioclient.depend import WAVEFORMATEX
from pycaw.pycaw import AudioUtilities, IAudioClient
from pycaw.utils import AudioDevice, AudioDeviceState, EDataFlow

log = logging.getLogger()

AUDCLNT_SHAREMODE_SHARED = 0
AUDCLNT_STREAMFLAGS_LOOPBACK = 0x00020000
AUDCLNT_STREAMFLAGS_AUTOCONVERTPCM = 0x80000000
REFERENCE_TIME_1SEC = 10_000_000

DEVICE_STATE_ACTIVE = 0x00000001

WAVE_FORMAT_IEEE_FLOAT = 0x0003
WAVE_FORMAT_EXTENSIBLE = 0xFFFE

# Define IAudioCaptureClient
class IAudioCaptureClient(IUnknown):
    _iid_ = GUID('{C8ADBD64-E71E-48a0-A4DE-185c395cd317}')
    _methods_ = (
        COMMETHOD(
            [], HRESULT, 'GetBuffer',
            (['out'], POINTER(c_void_p), 'data'),
            (['out'], POINTER(c_uint32), 'num_frames_to_read'),
            (['out'], POINTER(c_ulong), 'flags'),
            (['out'], POINTER(c_uint64), 'device_position'),
            (['out'], POINTER(c_uint64), 'qpc_position')
        ),
        COMMETHOD(
            [], HRESULT, 'ReleaseBuffer',
            (['in'], c_uint32, 'num_frames_to_read')
        ),
        COMMETHOD(
            [], HRESULT, 'GetNextPacketSize',
            (['out'], POINTER(c_uint32), 'num_frames_in_next_packet')
        ),
    )

class SamplesUnion(Structure):
    _fields_ = [
        ("wValidBitsPerSample", WORD),
        ("wSamplesPerBlock", WORD),
        ("wReserved", WORD),
    ]

class WAVEFORMATEXTENSIBLE(Structure):
    _fields_ = [
        ("Format", WAVEFORMATEX),
        ("Samples", SamplesUnion),
        ("dwChannelMask", DWORD),
        ("SubFormat", GUID),
    ]

class AudioCaptureImpl:
    def __init__(self, config, projectm_wrapper, sample_rate=44100, channels=2, samples=1024):
        self.projectm_wrapper = projectm_wrapper
        self.enumerator = AudioUtilities.GetDeviceEnumerator()

        self.audio_client = None
        self.capture_client = None
        self.channels = channels
        self.capture_active = False
        self.capture_restart = False

        self.capture_thread = threading.Thread(target=self._capture_thread, daemon=True)
        self.capture_thread.start()

        self.default_device_index = -1
        self.default_device_name = "Default Loopback"

        self.devices = self._enumerate_devices()
        self.device_index = -1

    def __del__(self):
        self.stop_recording()

    def _enumerate_devices(self):
        devices = AudioUtilities.GetAllDevices()

        filtered = [
            d for d in devices
            if d.state == AudioDeviceState.Active
        ]
        result = []
        for dev in filtered:

            props = dev.properties
            result.append({
                'device': dev,
                'name': dev.FriendlyName,
                'is_render': AudioUtilities.GetEndpointDataFlow(dev.id) == 0
            })
        return result

    def audio_device_list(self):
        return {i: d['name'] for i, d in enumerate(self.devices)} | {self.default_device_index: self.default_device_name}

    def audio_device_name(self):
        return self.audio_device_list().get(self.device_index, 'Unknown')

    def audio_device_index(self, idx: int):
        if idx < -1 or idx >= len(self.devices):
            return
        self.device_index = idx
        self.capture_restart = True

    def get_audio_device_list(self):
        def add_endpoints(device_list, data_flow):
            try:
                devices = self.enumerator.EnumAudioEndpoints(data_flow, DEVICE_STATE_ACTIVE)
                count = devices.GetCount()
                for i in range(count):
                    dev = devices.Item(i)
                    device_list.append(dev)
                    continue

                    dev_id = dev.GetId()
                    dev_state = dev.GetState()

                    # Extract properties into dict
                    props = {}
                    store = dev.OpenPropertyStore(0)  # STGM_READ
                    prop_count = store.GetCount()
                    for j in range(prop_count):
                        pk = store.GetAt(j)
                        try:
                            value = store.GetValue(pk).GetValue()
                            props[str(pk)] = value
                        except Exception:
                            # Some properties may fail—skip them gracefully
                            continue

                    is_render = (data_flow == EDataFlow.eRender)
                    device_list.append(AudioDevice(dev_id, dev_state, props, dev))

            except Exception as e:
                log.exception(f"Error enumerating devices: {e}")

        device_list = []
        add_endpoints(device_list, EDataFlow.eRender.value)
        add_endpoints(device_list, EDataFlow.eCapture.value)
        return device_list

    def start_recording(self, index):
        log.info('Start recording')
        self.device_index = index

        self.capture_active = True
        self.capture_restart = True

    def stop_recording(self):
        log.info('Stop recording')
        self.capture_active = False
        if self.capture_thread:
            self.capture_thread.join(timeout=1)

    def next_audio_device(self):
        total = len(self.devices)
        self.device_index = (self.device_index + 1 + total) % (total + 1) - 1
        self.capture_restart = True

    def open_audio_device(self, device, use_loopback):
        interface = device.Activate(IAudioClient._iid_, CLSCTX_ALL, None)
        self.audio_client = cast(interface, POINTER(IAudioClient))

        pwfx  = self.audio_client.GetMixFormat()

        if pwfx.contents.wFormatTag != WAVE_FORMAT_IEEE_FLOAT:
            extensibleFormat = cast(pwfx, POINTER(WAVEFORMATEXTENSIBLE)).contents

            if pwfx.contents.wFormatTag != WAVE_FORMAT_EXTENSIBLE:
                return False

            elif extensibleFormat.SubFormat != GUID('{00000003-0000-0010-8000-00AA00389B71}'):
                return False

        self.channels = pwfx.contents.nChannels

        hr = self.audio_client.Initialize(
            AUDCLNT_SHAREMODE_SHARED,
            AUDCLNT_STREAMFLAGS_LOOPBACK if use_loopback else 0,
            REFERENCE_TIME_1SEC,
            0,
            pwfx,
            None
        )

        if hr != 0:
            raise RuntimeError(f"Initialize failed with HRESULT: {hr:#x}")

        log.info(f"Initialized audio client with format: {pwfx.contents.nSamplesPerSec} Hz, {pwfx.contents.nChannels} channels {hr}")

        self.capture_client = cast(
            self.audio_client.GetService(IAudioCaptureClient._iid_),
            POINTER(IAudioCaptureClient)
            )

        self.audio_client.Start()

        return True

    def close_audio_device(self):
        if self.capture_client:
            self.capture_client = None

        if self.audio_client:
            self.audio_client = None
            self.capture_client = None

    def _capture_thread(self):
        try:
            CoInitializeEx(COINIT_MULTITHREADED)
            log.info("WASAPI thread started.")

            while True:
                if not self.capture_active:
                    time.sleep(0.1)
                    continue

                self.capture_restart = False

                devices = self.get_audio_device_list()
                use_loopback = True
                device_name = None

                if self.device_index == -1:
                    device = AudioUtilities.GetSpeakers()
                    device_name = self.default_device_name

                else:
                    device = devices[self.device_index]
                    use_loopback = AudioUtilities.GetEndpointDataFlow(device.GetId()) == 0
                    device_name = "Some Device"

                log.info(f"Attempting to open audio device: {type(device)} (channels: {self.channels}, loopback: {use_loopback})")

                if not self.open_audio_device(device, use_loopback):
                    self.capture_active = False

                log.info(f"Audio device opened: {type(device)} (channels: {self.channels}, loopback: {use_loopback})")
                while self.capture_active and not self.capture_restart:
                    try:
                        packet = self.capture_client.GetNextPacketSize()
                        while packet:
                            data_ptr, frames, flags, dev_pos, qvc_pos = self.capture_client.GetBuffer()
                            
                            if frames > 0:
                                try:
                                    raw_data = string_at(data_ptr, int(frames * ((self.channels * 32) / 8)))
                                    pcm = np.frombuffer(raw_data, dtype=np.float32)

                                    self.projectm_wrapper.add_pcm(pcm, channels=self.channels)
                                except OSError as e:
                                    log.exception(f"Access violation reading audio buffer: {e}")
                            else:
                                log.debug(f"Skipping buffer: frames={frames}, data_ptr={data_ptr}")

                            self.capture_client.ReleaseBuffer(frames)
                            packet = self.capture_client.GetNextPacketSize()
                        time.sleep(0.01)

                    except Exception as e:
                        log.exception(f"Error during capture: {e}")
                        raise

                log.info(f"Capture loop exited {self.capture_active} {self.capture_restart}")

                self.close_audio_device()
            
        except Exception as e:
            log.exception(f"Exception in capture thread: {e}")
        finally:
            CoUninitialize()
            log.info("WASAPI thread exited.")