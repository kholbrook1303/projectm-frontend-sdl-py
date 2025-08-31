import logging
import os
import threading

from core.projectMSDL.RenderingLoop import RenderingLoop

from lib.config import Config, APP_ROOT
from lib.log import log_init

log = logging.getLogger(__name__)

class ProjectMSDL:
    def __init__(self, config):
        self.config = config
        self.thread_event   = threading.Event()
        self.ctrl_threads   = list()

    def run(self):
        try:
            log.info('Starting projectMSDL rendering loop...')
            rendering_loop = RenderingLoop(self.config, self.thread_event)
            rendering_loop.run()
        except:
            log.exception('Failed to run rendering loop')
            self.thread_event.set()

    def close(self):
        if not self.thread_event.is_set():
            self.thread_event.set()
            
        log.info('Exiting ProjectMSDL!')

if __name__ == "__main__":
    config_path = os.path.join(APP_ROOT, 'projectMSDL.properties')
    config = Config(config_path)
    
    logpath = os.path.join(APP_ROOT, 'frontend-sdl-py.log')
    log_init(logpath, logging.DEBUG)
    log_init('console', logging.DEBUG)

    projectm_sdl = ProjectMSDL(config)
    projectm_sdl.run()
    projectm_sdl.close()
