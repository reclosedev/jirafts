import time

from jirafts import cli


if __name__ == "__main__":
    started = time.time()
    cli.main()
    print("Elapsed {:.3f} seconds".format(time.time() - started))
