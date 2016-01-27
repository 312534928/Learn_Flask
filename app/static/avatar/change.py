from PIL import Image
im=Image.open('2.jpg')
out=im.resize((25,25))
out.save('2_li.jpg')