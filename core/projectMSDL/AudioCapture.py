import logging
import os

if os.name == 'nt':
    from core.projectMSDL.AudioCaptureImpl_WASAPI import AudioCaptureImpl
else:
    from core.projectMSDL.AudioCaptureImpl_SDL import AudioCaptureImpl

log = logging.getLogger()

class AudioCapture:
    def __init__(self, config, projectm_wrapper):
        self.config = config
        self.projectm_wrapper = projectm_wrapper

        self.audio_capture_impl = AudioCaptureImpl(self.config, projectm_wrapper)
        deviceList = self.audio_capture_impl.audio_device_list()
        audioDeviceIndex = self.get_initial_audio_device_index(deviceList)

        self.output_device_list(deviceList)

        self.audio_capture_impl.start_recording(audioDeviceIndex)

    def __del__(self):
        if self.audio_capture_impl:
            self.audio_capture_impl.stop_recording()
            self.audio_capture_impl = None

    def output_device_list(self, deviceList):
        log.info(f'Available audio capturing devices:')

        for device in deviceList:
            log.info(f' - {device}: {deviceList[device]}')

    def get_initial_audio_device_index(self, deviceList):
        audioDeviceIndex = -1

        try:
            if not deviceList.get(audioDeviceIndex):
                audioDeviceIndex = -1
        except Exception as ex:
            log.error('audio.device is set to non-numerical value.')

        return audioDeviceIndex

    def next_audio_device(self):
        self.audio_capture_impl.next_audio_device()