# Автоматическое отключение symlinks при импорте
import os
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
os.environ['HF_HUB_DISABLE_SYMLINKS'] = '1'
os.environ['HF_HUB_ENABLE_HF_TRANSFER'] = '0'

try:
    import huggingface_hub
    from huggingface_hub import constants
    constants.HF_HUB_DISABLE_SYMLINKS = True
    constants.HF_HUB_ENABLE_HF_TRANSFER = False
except:
    pass
