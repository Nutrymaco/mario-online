from random import randint

def get_random_level(height=2000, width=800):
    init_level = [' '*width for _ in range(height)]

    for i in range(0, height, 2):
        block_size = randint(3, 12)
        block_start = randint(0, width - block_size)
        init_level[i] = init_level[i][:block_start] + '-' * block_size + init_level[i][block_start + block_size:]
    init_level[-1] = '-' * width
    return init_level