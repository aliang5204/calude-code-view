import os
from fastapi import APIRouter, HTTPException
from app.schemas import ReadFilesRequest, ScanDirRequest
from app.services.context import read_files_content, scan_directory

router = APIRouter(prefix="/api/context", tags=["context"])


@router.post("/read-files")
async def read_files(data: ReadFilesRequest):
    """读取指定文件内容"""
    return read_files_content(data.paths)


@router.post("/scan-dir")
async def scan_dir(data: ScanDirRequest):
    """扫描目录结构"""
    if not os.path.isdir(data.path):
        raise HTTPException(status_code=400, detail=f"Directory not found: {data.path}")
    tree = scan_directory(data.path, max_depth=data.max_depth)
    return {"tree": tree}
