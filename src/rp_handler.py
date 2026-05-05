from BinPack import BinPack

import packaide

import runpod

def handler(job):
    myBinPack = BinPack()

    # if 'parts' in job["input"]:
    #     return {"error": f"handler: Please provide at least one part. {job}"}

    if 'stock' in job["input"]:
        myBinPack.stock = job["input"]['stock']
        irregular_stock_bins, parts = myBinPack.make_irregular_stock(bin = job["input"]['stock'], parts = job["input"]['parts'])
        result = myBinPack.pack(bins=irregular_stock_bins, parts=parts)
    else:
        # If not bin is supplied
        result = myBinPack.pack(bins=None, parts = job["input"]['parts'])

    if 'id' in job["input"]:
        result.id = job["id"]

    return result


# Start the handler only if this script is run directly
if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
