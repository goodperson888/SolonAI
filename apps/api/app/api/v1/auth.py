from fastapi import APIRouter

router = APIRouter()

@router.post("/login")
async def login():
    """
    用户登录

    TODO: 实现钱包签名验证登录逻辑
    """
    return {"message": "登录接口 - 待实现"}

@router.post("/verify")
async def verify_wallet():
    """
    验证钱包地址

    TODO: 实现钱包地址验证逻辑
    """
    return {"message": "钱包验证接口 - 待实现"}
