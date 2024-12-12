import time
import cv2
import numpy as np
import pywt
import pywt.data
import tkinter as tk
from tkinter import filedialog
import matplotlib.pyplot as plt


quantization_table = np.array([
        [16, 11, 10, 16, 24, 40, 51, 61],
        [12, 12, 14, 19, 26, 58, 60, 55],
        [14, 13, 16, 24, 40, 57, 69, 56],
        [14, 17, 22, 29, 51, 87, 80, 62],
        [18, 22, 37, 56, 68, 109, 103, 77],
        [24, 35, 55, 64, 81, 104, 113, 92],
        [49, 64, 78, 87, 103, 121, 120, 101],
        [72, 92, 95, 98, 112, 100, 103, 99],
    ])


def dct_matrix(N):
    dct = np.zeros((N, N))
    for i in range(N):
        for j in range(N):
            alpha = np.sqrt(1 / N) if i == 0 else np.sqrt(2 / N)
            dct[i, j] = alpha * np.cos(np.pi / N * (j + 0.5) * i)
    return dct



def compress_dct(image, block_size=8):
    height, width = image.shape
    compressed_image = np.zeros_like(image, dtype=np.float32)
    dct_matrix_block = dct_matrix(block_size)
    
    for i in range(0, height, block_size):
        for j in range(0, width, block_size):
            block = image[i:i+block_size, j:j+block_size]
            
            # DCT
            block_dct = np.dot(np.dot(dct_matrix_block, block), dct_matrix_block.T)
            
            # Quantization
            block_dct = np.round(block_dct / quantization_table)
            
            # Dequantization
            block_dct = block_dct * quantization_table
            
            # Inverse DCT
            compressed_image[i:i+block_size, j:j+block_size] = np.dot(
                np.dot(dct_matrix_block.T, block_dct), dct_matrix_block
            )
    return np.clip(compressed_image, 0, 255).astype(np.uint8)


# Функція для виконання стиснення з використанням DWT (Хаара)
def compress_dwt(image, wavelet='haar', threshold=0.1):
    
    coeffs2 = pywt.dwt2(image, wavelet)
    LL, (LH, HL, HH) = coeffs2
    
    LH = np.where(np.abs(LH) > threshold, LH, 0)
    HL = np.where(np.abs(HL) > threshold, HL, 0)
    HH = np.where(np.abs(HH) > threshold, HH, 0)
    
    compressed_image = pywt.idwt2((LL, (LH, HL, HH)), wavelet)
    return np.uint8(compressed_image)


# Функція для обчислення MSE
def calculate_mse(original, compressed):
    assert original.shape == compressed.shape, "Зображення повинні мати однаковий розмір!"
    mse = np.mean((original - compressed) ** 2)
    return mse

# Функція для обчислення PSNR
def calculate_psnr(original, compressed):
    mse = calculate_mse(original, compressed)
    
    if mse == 0:
        return 100
    
    # Максимальне значення пікселів для 8-бітного зображення
    max_pixel = 255.0
    
    # Обчислення PSNR
    psnr_value = 10 * np.log10((max_pixel ** 2) / mse)
    return psnr_value


# Функція для завантаження зображення
def load_image():
    file_path = filedialog.askopenfilename()
    return cv2.resize(cv2.imread(file_path, cv2.IMREAD_GRAYSCALE), (512, 512)) if file_path else None
    
def load_and_compress():
    original_image = load_image()
    if original_image is None:
        return
    start_time = time.time()
    dct_compressed = compress_dct(original_image)
    end_time = time.time()
    print(f'DCT compression time:{end_time-start_time}')
    dct_psnr = calculate_psnr(original_image, dct_compressed)

    start_time = time.time()
    dwt_compressed = compress_dwt(original_image)
    end_time = time.time()
    
    print(f'DWT compression time:{end_time-start_time}')
    dwt_psnr = calculate_psnr(original_image, dwt_compressed)
    
    # Виведення результатів
    _, ax = plt.subplots(1, 3, figsize=(15, 5))
    ax[0].imshow(original_image, cmap='gray')
    ax[0].set_title('Original Image')
    ax[0].axis('off')

    ax[1].imshow(dct_compressed, cmap='gray')
    ax[1].set_title(f'DCT Compressed (PSNR: {dct_psnr:.2f})')
    ax[1].axis('off')

    ax[2].imshow(dwt_compressed, cmap='gray')
    ax[2].set_title(f'DWT Compressed (PSNR: {dwt_psnr:.2f})')
    ax[2].axis('off')

    plt.show()

# Графічний інтерфейс
def show_interface():
    root = tk.Tk()
    root.title('Image Compression using DCT and DWT')
    
    btn_load = tk.Button(root, text="Load and Compress Image", command=load_and_compress)
    btn_load.pack(pady=20)
    
    root.mainloop()

if __name__ == '__main__':
    show_interface()
