from fastapi import APIRouter

import aliyunpan
import logging

router = APIRouter()
logger = logging.getLogger()


@router.post("/", summary="根据路径获取播放链接")
def get_download_url(path: dict):
    """
    根据路径获取播放链接
    """
    logger.info(f"path::: {path}")
    logger.info("api逻辑未启用")
    # print(path)
    # alipan = aliyunpan.AliyunPan()
    # return {"code": 0, "data": alipan.get_download_url(path.get("dest_dir"))}
