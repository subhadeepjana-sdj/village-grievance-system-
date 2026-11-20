content = open("frontend/src/pages/LandingPage_template.txt", "r", encoding="utf-8").read()
open("frontend/src/pages/LandingPage.jsx", "w", encoding="utf-8").write(content)
print("done", len(content))
