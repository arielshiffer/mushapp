import kivy
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.core.audio import SoundLoader
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput

class MusicPlayer(App):
    def build(self):
        self.song_name = "Song.mp3"
        self.sound = None

        layout = GridLayout(cols=1)

        play_button = Button(text='Play', on_press=self.play_song)
        check_button = Button(text='check', on_press=self.check)
        self.song_label = Label(text=self.song_name)
        song_input = TextInput(text=self.song_name, multiline=False, on_text_validate=self.change_song)
        layout.add_widget(song_input)
        layout.add_widget(check_button)
        layout.add_widget(self.song_label)
        layout.add_widget(play_button)

        self.root = layout

    def play_song(self, instance):
        print(self.song_name)
        if self.sound:
            self.sound.play()

    def check(self, instance):
        pass


    def change_song(self, instance):
        new_song_name = instance.text
        if new_song_name != self.song_name:
            self.song_name = new_song_name
            if self.sound:
                self.sound.stop()
            self.sound = SoundLoader.load(self.song_name)
            self.song_label.text = self.song_name  # Update the song label
            self.sound_position = 0.0
            self.paused = False

if __name__ == '__main__':
    MusicPlayer().run()
