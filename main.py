import pygame
import pyaudio
import numpy as np


class ImageTransformation:
    def __init__(self, img_path, size, d_size, max_size, min_size, screen_size):
        self.original_img = pygame.image.load(img_path)
        self.img = pygame.image.load(img_path)
        self.original_size = size
        self.size = size
        self.d_size = d_size
        self.max_size = max_size
        self.min_size = min_size
        self.screen_size = screen_size
        self.growing = True

    def update_pulse(self):
        if self.size > self.max_size:
            self.growing = False
        if self.size < self.min_size:
            self.growing = True

        self.size = self.size + self.d_size if self.growing else self.size - self.d_size
        print(self.size)

        self.img = pygame.transform.scale(self.original_img, (self.size, self.size))

    def update_delta(self, d_factor):
        bars = "#" * int(d_factor * self.d_size)
        print(bars)

        self.size = self.original_size + int(self.d_size * d_factor)
        self.img = pygame.transform.scale(self.original_img, (self.size, self.size))

    def get_center(self):
        return (self.screen_size[0] - self.size) // 2, (self.screen_size[1] - self.size) // 2


def calculate_volume_value(stream_data):
    data = np.fromstring(stream_data, dtype='b')
    data_abs = np.abs(data)

    # normalize data between 0 and 1
    data_norm = data_abs / 127

    # calculate mean of data to represent overall volume
    data_max = np.max(data_norm)
    data_mean = np.mean(data_norm)

    return data_max, data_mean


def calculate_frequency_value(stream_data, lower_bound, upper_bound):
    data = np.fromstring(stream_data, dtype=np.int16)

    # calculate absolute fast fourier transformation
    data_freq = np.abs(np.fft.fft(data))

    # calculate fast fourier frequencies
    freq = np.fft.fftfreq(len(data))

    # calculate frequencies in hertz
    data_freq_hertz = data_freq * freq

    # cut half because of real symmetry
    data_freq_hertz_rel = data_freq_hertz[0:(len(data_freq_hertz) // 2)]

    # normalize between 0 and 1
    data_freq_hertz_rel_norm = (data_freq_hertz_rel - np.min(data_freq_hertz_rel)) / (
                np.max(data_freq_hertz_rel) - np.min(data_freq_hertz_rel))

    # extract frequency area
    bass_freq = data_freq_hertz_rel_norm[lower_bound:upper_bound]

    # calculate maximum and mean of frequency area
    bass_freq_max = np.max(bass_freq)
    bass_freq_mean = np.mean(bass_freq)

    return bass_freq_max, bass_freq_mean


def loop():
    # initialize pygame
    pygame.init()
    # screen_size = (1000, 1000)
    # screen = pygame.display.se0t_mode((screen_size, screen_size))
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    screen_size = screen.get_size()

    # initialize image transformation
    img_path = 'assets/logo_fox.png'
    img_size = screen_size[1] // 2
    delta_size = img_size * 5
    max_size = screen_size[0]
    min_size = screen_size[1] // 10
    img_transform = ImageTransformation(img_path, img_size, delta_size, max_size, min_size, screen_size)

    # initialize audio recording
    out_format = pyaudio.paInt16
    channels = 2

    rate = 44100
    chunk = 4096

    lower_bass_bound = 0
    upper_bass_bound = 10
    lower_treble_bound = 500
    upper_treble_bound = 1000

    audio = pyaudio.PyAudio()
    stream = audio.open(format=out_format, channels=channels,
                        rate=rate, input=True,
                        frames_per_buffer=chunk)

    running = True
    while running:

        # Did the user click the window close button?
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # read audio input
        stream_data = stream.read(chunk)

        volume_value_max, volume_value_mean = calculate_volume_value(stream_data)
        bass_value_max, bass_value_mean = calculate_frequency_value(stream_data, lower_bass_bound, upper_bass_bound)
        treble_value_max, treble_value_mean = calculate_frequency_value(stream_data, lower_treble_bound, upper_treble_bound)

        # reset screen with black
        screen.fill((0, 0, 0))

        # image transformation
        # img_transform.update_pulse()
        img_transform.update_delta(bass_value_mean)
        screen.blit(img_transform.img, (img_transform.get_center()[0], img_transform.get_center()[1]))

        # update the display
        pygame.display.flip()
        # running = False

    pygame.quit()


if __name__ == "__main__":
    loop()
