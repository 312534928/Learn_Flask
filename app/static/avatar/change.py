from PIL import Image
import glob


def resizeMid(target, size):
    imgList = glob.glob(target)
    for path in imgList:
        pathMid=path.replace(".jpg","_mid.jpg")
        if not glob.glob(pathMid):
            im = Image.open(path)
            out = im.resize(size,Image.ANTIALIAS)
            out.save(pathMid)


def resizeLi(target, size):
    imgList = glob.glob(target)
    for path in imgList:
        pathLi=path.replace(".jpg","_li.jpg")
        if not glob.glob(pathLi):
            im = Image.open(path)
            out = im.resize(size,Image.ANTIALIAS)
            out.save(pathLi)

if __name__ == '__main__':
    little = (25, 25)
    mid = (50, 50)
    target = './[!_].jpg'
    resizeLi(target,little)
    resizeMid(target,mid)
    # im = Image.open(".\\1.jpg")
    # out=im.resize(mid,Image.LANCZOS)
    # out.save(".\\1_mid.jpg")
