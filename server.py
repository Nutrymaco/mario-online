import redis

def server():

    r_in = redis.Redis()
    r_out = redis.Redis()
    while True:
        players = r_in.keys('player_*')
        level = r_in.keys('level')
        if level:
            r_out.set('level', r_in.get('level'))
        for player in players:
            x, y = r_out.hget(player, 'x'), r_out.hget(player, 'y')
            r_out.hset(player, 'x', x)
            r_out.hset(player, 'y', y)



if __name__ == '__main__':
    server()