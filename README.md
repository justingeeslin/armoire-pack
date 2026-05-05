# BinPack (RunPod Worker)

## Local Building and Testing
```bash
docker build -t runpod-pack . 
```
```bash
docker run runpod-pack > run.txt
```

### Adding new tests
Inside `src`, create a new JSON input.
In `start.sh`, Add a call to rp_handler to run that JSON input.