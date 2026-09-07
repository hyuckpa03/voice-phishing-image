from analyze_image import analyze_phishing_image
import json

if __name__ == "__main__":
    # a_phishing.jpg 를 c_long.jpg 로 변경
    result = analyze_phishing_image("samples/c_long.jpg")
    
    print(json.dumps(result, indent=2, ensure_ascii=False))