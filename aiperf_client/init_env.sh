export PYTHONPATH=/home/aiperf/aiperf_client/aiperf_inferencex_754356e9/src:/home/aiperf/aiperf_client/aiperf-k3-c16-py
export HF_DATASETS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false
export AIPERF_DATASET_CONFIGURATION_TIMEOUT=1800
export AIPERF_SERVICE_PROFILE_CONFIGURE_TIMEOUT=2100

python3 -c "import aiperf; print(aiperf.__file__)"
