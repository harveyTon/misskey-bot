"""
验证码生成器 - 优化版
"""
import random
import string
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from captcha.image import ImageCaptcha

def generate_captcha_text(length=4):
    """
    生成随机验证码文本
    
    参数:
        length (int): 验证码长度，默认为4位，更容易识别
    
    返回:
        str: 随机生成的验证码文本
    """
    # 只使用容易区分的字符，避免混淆
    # 排除容易混淆的字符: 0, O, 1, I, l, 9, g, q
    characters = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789abcdefhijkmnprstuvwxyz'
    return ''.join(random.choice(characters) for _ in range(length))

def generate_captcha_image_with_custom_options(text):
    """
    使用自定义选项生成更易于识别的验证码图片
    
    参数:
        text (str): 验证码文本
    
    返回:
        BytesIO: 包含验证码图片的字节流
    """
    # 设置图片尺寸和背景色
    width = 160
    height = 60
    bg_color = (255, 255, 255)  # 白色背景
    
    # 创建图片对象
    image = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(image)
    
    # 尝试加载字体，如果失败则使用默认字体
    try:
        # 使用更清晰的字体
        font = ImageFont.truetype('Arial', 36)
    except IOError:
        font = ImageFont.load_default()
    
    # 计算文本位置，使其居中
    text_width = font.getbbox(text)[2]
    text_height = font.getbbox(text)[3]
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    # 绘制文本，使用深色
    text_color = (0, 0, 200)  # 深蓝色
    draw.text((x, y), text, font=font, fill=text_color)
    
    # 添加一些干扰线，但不要太多
    for i in range(3):
        line_color = (random.randint(100, 200), random.randint(100, 200), random.randint(100, 200))
        start_x = random.randint(0, width // 3)
        start_y = random.randint(0, height)
        end_x = random.randint(width // 3 * 2, width)
        end_y = random.randint(0, height)
        draw.line([(start_x, start_y), (end_x, end_y)], fill=line_color, width=1)
    
    # 添加一些干扰点，但密度较低
    for i in range(30):
        dot_color = (random.randint(100, 200), random.randint(100, 200), random.randint(100, 200))
        x = random.randint(0, width)
        y = random.randint(0, height)
        draw.point((x, y), fill=dot_color)
    
    # 轻微模糊，使图像更平滑
    image = image.filter(ImageFilter.SMOOTH)
    
    # 将图片转换为字节流
    image_bytes = BytesIO()
    image.save(image_bytes, format='PNG')
    image_bytes.seek(0)
    
    return image_bytes

def generate_captcha_image_with_library(text):
    """
    使用captcha库生成验证码图片，但使用更友好的配置
    
    参数:
        text (str): 验证码文本
    
    返回:
        BytesIO: 包含验证码图片的字节流
    """
    # 创建验证码生成器，使用更大的尺寸和更清晰的字体
    image = ImageCaptcha(
        width=160,         # 适当的宽度
        height=60,         # 适当的高度
        fonts=['Arial'],   # 使用清晰的字体
        font_sizes=(42,)   # 更大的字体尺寸
    )
    
    # 生成验证码图片
    captcha_image = image.generate(text)
    
    # 将图片转换为字节流
    image_bytes = BytesIO()
    image_bytes.write(captcha_image.getvalue())
    image_bytes.seek(0)
    
    return image_bytes

def generate_captcha_image(text):
    """
    生成验证码图片，尝试使用自定义方法，如果失败则回退到库方法
    
    参数:
        text (str): 验证码文本
    
    返回:
        BytesIO: 包含验证码图片的字节流
    """
    try:
        # 尝试使用自定义方法
        return generate_captcha_image_with_custom_options(text)
    except Exception as e:
        # 如果自定义方法失败，回退到使用库的方法
        print(f"自定义验证码生成失败: {e}，使用库方法")
        return generate_captcha_image_with_library(text)

def generate_captcha():
    """
    生成验证码文本和图片
    
    返回:
        tuple: (验证码文本, 验证码图片字节流)
    """
    captcha_text = generate_captcha_text()
    captcha_image = generate_captcha_image(captcha_text)
    return captcha_text, captcha_image 