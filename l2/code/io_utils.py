import os
import math
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image, ImageEnhance


def get_int(file, number_of_bytes):
    return int.from_bytes(
        file.read(number_of_bytes), 
        byteorder='big',
        signed=False)

def get_data_from_idx_labels_file(filename: str):
    with open(filename, 'rb') as f:
        magic_number = get_int(f, 4)
        number_of_items = get_int(f, 4)
        data = np.empty(number_of_items)
        for i in range(number_of_items):
            data[i] = get_int(f, 1)
        return data

def get_data_from_idx_images_file(filename: str):
    with open(filename, 'rb') as f:
        magic_number = get_int(f, 4)
        number_of_images = get_int(f, 4)
        number_of_rows = get_int(f, 4)
        number_of_cols = get_int(f, 4)
        data = np.empty((number_of_images, number_of_rows, number_of_cols))
        for i in range(number_of_images):
            for r in range(number_of_rows):
                for c in range(number_of_cols):
                    data[i, r, c] = get_int(f, 1)
    return data

def get_mnist_data():
    data_dir = os.path.join(
            os.path.abspath(
                os.path.dirname(
                    os.path.dirname(__file__)
                )
            ), 'dataset', 'mnist')
    print('Downloading MNIST dataset ...')
    ds_train_labels = get_data_from_idx_labels_file(os.path.join(data_dir, 'train-set-labels.idx'))
    print(f'Downloaded training labels {ds_train_labels.shape}')
    ds_train_images = get_data_from_idx_images_file(os.path.join(data_dir, 'train-set-images.idx'))
    print(f'Downloaded training images {ds_train_images.shape}')
    ds_test_labels  = get_data_from_idx_labels_file(os.path.join(data_dir, 'test-set-labels.idx'))
    print(f'Downloaded test labels {ds_test_labels.shape}')
    ds_test_images  = get_data_from_idx_images_file(os.path.join(data_dir, 'test-set-images.idx'))
    print(f'Downloaded test images {ds_test_images.shape}')
    ds_train_images = ds_train_images / 255.0
    ds_test_images  = ds_test_images  / 255.0
    return (ds_train_images, ds_train_labels, ds_test_images, ds_test_labels)

def extract_data_from_photo(img_path: str, preprocess: bool):
    ############################ read pixels ##################################
    im = Image.open(img_path, 'r')
    im = ImageEnhance.Contrast(im).enhance(10)
    ########################## default preprocess #############################
    if not preprocess:
        im = im.resize((28, 28))
        pixels = [[1 for _ in range(28)] for _ in range(28)]
        i = 0
        for pixel in im.getdata():
            # convert to grayscale
            p = 0.299 * pixel[0] + 0.587 * pixel[1] + 0.114 * pixel[2]
            # normalize
            p = p/255.0
            # enhance
            p = 0 if p < 0.1 else 1
            # negate
            p = 1 - p
            # save
            pixels[int(i/28)][int(i%28)] = p
            i += 1
        return pixels
    ########################## advanced preprocess ############################
    w, h = im.size
    pixels = [[1 for _ in range(w)] for _ in range(h)]
    i = 0
    for pixel in im.getdata():
        # convert to grayscale
        p = 0.299 * pixel[0] + 0.587 * pixel[1] + 0.114 * pixel[2]
        # normalize
        p = p/255.0
        # enhance black white difference
        p = 0 if p < 0.1 else 1
        # save
        pixels[int(i/w)][int(i%w)] = p
        i += 1
    ########################### find bounding box #############################
    # top border
    try:
        for row_index_top, row in enumerate(pixels):
            for pixel in row:
                if pixel < 0.1:
                    raise ValueError('Found bounding box')
    except ValueError: pass
    # bottom border
    try:
        for row_index_bottom, row in enumerate(pixels[::-1]):
            for pixel in row:
                if pixel < 0.1:
                    raise ValueError('Found bounding box')
    except ValueError: pass
    # left border
    try:
        for col_index_left in range(len(pixels[0])):
            for i in range(len(pixels)):
                if pixels[i][col_index_left] < 0.1:
                    raise ValueError('Found bounding box')
    except ValueError: pass
    # right border
    try:
        for col_index_right in range(len(pixels[0])-1, 0, -1):
            for i in range(len(pixels)):
                if pixels[i][col_index_right] < 0.1:
                    raise ValueError('Found bounding box')
    except ValueError: pass
    if col_index_left < col_index_right:
        if row_index_top < len(pixels) - row_index_bottom:
            pixels = [[p for p in row[col_index_left:col_index_right]] for row in pixels[row_index_top:len(pixels)-row_index_bottom]]
    ########################## convert to (20 x 20) ###########################
    w = len(pixels[0])
    h = len(pixels)
    im = Image.new('L', (w, h))
    im.putdata(sum(pixels, []))
    scaled_pixels = []
    scale = max(w, h) / 20
    w = math.ceil(w/scale)
    h = math.ceil(h/scale)
    im = im.resize((w, h), Image.ANTIALIAS)
    w, h = im.size
    scaled_pixels = im.getdata()
    ################################# negate ##################################
    enhanced_pixels = []
    for p in scaled_pixels:
        p = 1 - p
        enhanced_pixels.append(p)
    ########################### fill to (28 x 28) #############################
    empty_pixels = [[0.0 for _ in range(28)] for _ in range(28)]
    i = 0
    while i < h:
        j = 0
        while j < w:
            p = enhanced_pixels[w*i+j]
            empty_pixels[int((28-h)/2) + i][int((28-w)/2) + j] = p
            j += 1
        i += 1
    
    return empty_pixels

def get_photos_data(folder: str, preprocess=False):
    data_dir = os.path.join(
                os.path.dirname(
                    os.path.dirname(
                        os.path.abspath(__file__)
                    )
                ), 'dataset', folder)
    print(f'Preparing data from {data_dir}')
    ds_images = []
    ds_labels = []
    for img in sorted(os.listdir(data_dir)):
        if img.endswith('.jpg') or img.endswith('.png'):
            ds_images.append(extract_data_from_photo(os.path.join(data_dir, img), preprocess))
            ds_labels.append(int(img.split('_')[0]))
    return (np.array(ds_images).astype('float32'),
            np.array(ds_labels).astype('float32'))


if __name__ == '__main__':
    data = extract_data_from_photo('../dataset/my_1/0_1.png', True)
    plt.imshow(data)
    plt.show()
    plt.clf()
    plt.close()
