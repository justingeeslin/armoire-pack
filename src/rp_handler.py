from BinPack import BinPack

import packaide

import runpod

def handler(job):
    myBinPack = BinPack()
    myBinPack.parts = job["input"]['parts']
    myBinPack.bin = job["input"]['bin']
    return myBinPack.pack()


# Start the handler only if this script is run directly
if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
