import os
import numpy as np
import pygame.midi
import threading
from PIL import Image
from tkinter import Label, Listbox, Tk, Button, filedialog, messagebox, Scrollbar
from tkinter import font as tkfont
from mido import MidiFile, MidiTrack, Message


MIDI_FILES_DIR = 'generated_midi_files'

file_list = []
current_player = None
playback_thread = None 

playback_lock = threading.RLock()

def image_to_midi(image_path:str, output_filename:str) -> None:
    image = Image.open(image_path).convert('L') # конвертація пікселів зображення в градації сірого
    image_data = np.array(image)

    normalized_data = np.interp(image_data, (0,255),(21,108)).astype(int)  # нормалізація даних в діапазон нот фортепіано

    midi_file = MidiFile()
    track = MidiTrack()
    midi_file.tracks.append(track)

    block_size = 8
    for i in range(0, normalized_data.shape[0], block_size):
        for j in range(0, normalized_data.shape[1], block_size):
            block = normalized_data[i:i+block_size, j:j+block_size]
            note = int(np.mean(block)) 
            track.append(Message(type='note_on', note=note, velocity=127, time=120))
            track.append(Message(type='note_off', note=note, velocity=127, time=120))
    
    midi_file.save(output_filename)
    update_file_list()
    messagebox.showinfo('Success', f'MIDI file {output_filename} successfully saved in directory {MIDI_FILES_DIR}')

def choose_image():
    image_path = filedialog.askopenfilename(title='Choose an image',
                                           filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")])
    
    if image_path:
        try:
            filename = ''
            for filename_part in os.path.basename(image_path).split('.')[:-1]:
                filename += filename_part
            filename+='.mid'
            output_filename = os.path.join(MIDI_FILES_DIR, filename)
            os.makedirs(MIDI_FILES_DIR, exist_ok=True)
            midi_generation_thread = threading.Thread(target=image_to_midi, args=(image_path, output_filename), daemon=True)
            midi_generation_thread.start()
        except Exception as e:
            messagebox.showerror('Error', f'Error during sonification of file {filename}:{e}')
    

def update_file_list():
    global file_list
    file_list.delete(0, 'end')
    if os.path.exists(MIDI_FILES_DIR):
        for file in os.listdir(MIDI_FILES_DIR):
            if file.endswith('.mid'):
                file_list.insert('end', file)


def play_midi_file():
    global current_player
    try:
        selected_file = file_list.get(file_list.curselection())
        midi_file_path = os.path.join(MIDI_FILES_DIR, selected_file)
        with playback_lock:
            if current_player:
                current_player.close()
                pygame.midi.quit()
                current_player = None
            
        midi_file = MidiFile(midi_file_path)
        with playback_lock:
            pygame.midi.init()
            current_player = pygame.midi.Output(0)       
        for msg in midi_file.play():
            with playback_lock:
                if not current_player:
                    break
            if not msg.is_meta:
                if msg.type == 'note_on':
                    current_player.note_on(msg.note, msg.velocity)
                elif msg.type == 'note_off':
                    current_player.note_off(msg.note, msg.velocity)


        with playback_lock:
            if current_player:
                current_player.close()
                current_player = None
                pygame.midi.quit()
    except Exception as e:
        messagebox.showerror('Error', f'Can not open and play MIDI file:{e}')

def play_midi():
    playback_thread = threading.Thread(target=play_midi_file, daemon=True)
    playback_thread.start()


def main():
    global file_list
    
    root = Tk()
    root.title("Image Sonification")
    root.geometry("600x400")
    root.config(bg="#f0f0f0")

    
    header_font = tkfont.Font(family="Helvetica", size=14, weight="bold")
    button_font = tkfont.Font(family="Helvetica", size=12)
    label_font = tkfont.Font(family="Helvetica", size=10)

    
    Button(root, text="Choose Image File", command=choose_image, font=button_font, width=20, bg="#4CAF50", fg="white", relief="raised").pack(pady=15)

   
    Label(root, text="Saved MIDI Files:", font=header_font, bg="#f0f0f0").pack(pady=10)

    
    file_list_frame = Label(root, bg="#f0f0f0")
    file_list_frame.pack(pady=5)

    file_list_scrollbar = Scrollbar(file_list_frame)
    file_list_scrollbar.pack(side="right", fill="y")

    file_list = Listbox(file_list_frame, width=50, height=10, font=label_font, selectmode="single", bg="#ffffff", yscrollcommand=file_list_scrollbar.set)
    file_list.pack(side="left", padx=10)

    file_list_scrollbar.config(command=file_list.yview)

    
    Button(root, text="Play Selected MIDI", command=play_midi, font=button_font, width=20, bg="#2196F3", fg="white", relief="raised").pack(pady=20)

    
    update_file_list()

    
    root.mainloop()

if __name__ == '__main__':
    main()