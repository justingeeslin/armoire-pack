from BinPack import BinPack

import packaide

import runpod




def handler(job):
    job_input = job["input"]

    # basic validation for required arg
    if "parts" not in job_input:
        return {"error": "Missing required parameter 'parts'"}

    return pack(**job_input)


# Start the handler only if this script is run directly
if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
