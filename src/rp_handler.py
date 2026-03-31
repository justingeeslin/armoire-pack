from BinPack import BinPack

import packaide

import runpod

def handler(job):
    myBinPack = BinPack()

    myBinPack.parts = job["input"]['parts']

    if 'stock' in job["input"]:
        # When a custom bin is supplied, apply it and make irregular stock before packing
        myBinPack.stock = job["input"]['stock']
        # The first stock is the inital bin
        myBinPack.bin = myBinPack.stock

        result = myBinPack.make_irregular_stock_then_pack()
    else:
        # If not bin is supplied us the default one and pack
        result = myBinPack.pack()

    return result


# Start the handler only if this script is run directly
if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
