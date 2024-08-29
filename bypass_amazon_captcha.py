from amazoncaptcha import AmazonCaptcha

link = 'https://images-na.ssl-images-amazon.com/captcha/usvmgloq/Captcha_kwrrnqwkph.jpg'

captcha = AmazonCaptcha.fromlink(link)
solution = captcha.solve()
print(solution)