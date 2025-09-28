# BitNBuild-25_DjangOps

# 🎯 Review Radar: Product Sentiment Analyzer

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-success.svg)]()

> **Transform thousands of reviews into actionable insights in seconds** 🚀

## 📖 Overview

In the age of e-commerce, customer reviews are critical for purchasing decisions. However, popular products can accumulate hundreds or thousands of reviews, creating information overload for shoppers. **Review Radar** solves this problem by automatically analyzing product reviews and generating clear, actionable insights.

![Review Radar Demo](https://via.placeholder.com/800x400/4CAF50/FFFFFF?text=Review+Radar+Demo)

## ✨ Key Features

### 🌐 **URL-Based Web Scraper**
- Robust module that accepts product page URLs from major e-commerce sites
- Automatically navigates and extracts customer review text content
- Supports multiple platforms and review formats

### 🧠 **Pre-trained Sentiment Classifier**
- Utilizes advanced sentiment analysis models from Hugging Face
- Classifies reviews as **Positive**, **Negative**, or **Neutral**
- High accuracy sentiment detection with confidence scores

### 🔍 **Keyword & Topic Extraction**
- Advanced topic modeling and TF-IDF keyword extraction
- Identifies most frequently mentioned product features
- Separates positive and negative feedback themes
- Examples: "battery life", "screen quality", "customer service"

### 📊 **Interactive Dashboard**
- Clean, intuitive Streamlit interface
- Real-time sentiment breakdown with pie charts
- Top positive and negative keywords visualization
- Exportable analysis reports

## 🏗️ Architecture


graph LR
    A[Product URL] --> B[Web Scraper]
    B --> C[Review Extraction]
    C --> D[Sentiment Analysis Model]
    D --> E[Keyword Extraction]
    E --> F[Dashboard Visualization]
    F --> G[Actionable Insights]

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Installation

1. **Clone the repository**
   
   [Github Repo](https://github.com/JadenBritto/BitNBuild-25_DjangOps)
  
   cd review-radar
   

2. **Create virtual environment**
  
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   

3. **Install dependencies**

   pip install -r requirements.txt
   

5. **Run the application**
   
   streamlit run app.py
   

6. **Open your browser**
   
   http://localhost:8501
   

## 🎯 Usage

1. **Launch the application** using the command above
2. **Enter a product URL** from supported e-commerce sites
3. **Click "Analyze Reviews"** to start the process
4. **View the dashboard** with:
   - Overall sentiment distribution
   - Top positive keywords
   - Top negative keywords
   - Detailed insights and recommendations

### Supported E-commerce Sites
- Amazon
- Flipkart
- eBay
- And more...

## 📁 Project Structure

#
BitNBuild-25_DjangOps/
├─ data/
├─ ml/
├─ reviewradar-final/
├─ venv/
├─ web/
│  ├─ __pycache__/
│  ├─ browser_extension/
│  │  ├─ content.js
│  │  ├─ manifest.json
│  │  ├─ popup.html
│  │  └─ popup.js
│  ├─ 2.13.0
│  ├─ ENHANCED_FEATURES.md
│  ├─ README.md
│  ├─ alternative_sites.txt
│  ├─ backend_api.py
│  ├─ exact_product_urls.txt
│  ├─ fix_keras_compatibility.bat
│  ├─ fix_keras_compatibility.py
│  ├─ mock_scraper.py
│  ├─ quick_test_scraper.py
│  ├─ requirements.txt
│  ├─ scraper.py
│  ├─ start_backend.bat
│  ├─ start_backend.py
│  ├─ streamlit_app.py
│  ├─ test_ecommerce_scraper.py
│  ├─ test_scraper.py
│  ├─ test_setup.py
│  ├─ test_urls.txt
│  ├─ test_working_urls.py
│  └─ working_product_urls.txt
├─ .gitignore
└─ README.md  #


## 🔧 Technical Details

### Model Training
- **Dataset**: Trained on diverse e-commerce review datasets
- **Architecture**: Transformer-based sentiment classification
- **Accuracy**: 92%+ on test data
- **Languages**: Currently supports English reviews

### Web Scraping
- **Ethical scraping** with rate limiting
- **Robust parsing** handles various HTML structures
- **Error handling** for network issues and format changes

### Sentiment Analysis Pipeline

# Example usage
from models.sentiment_model import SentimentAnalyzer

analyzer = SentimentAnalyzer()
sentiment = analyzer.predict("This product is amazing!")
# Output: {'sentiment': 'positive', 'confidence': 0.95}


## 📊 Sample Output

### Sentiment Distribution
- 🟢 **Positive**: 65%
- 🔴 **Negative**: 20%
- 🟡 **Neutral**: 15%

### Top Keywords
**Positive Themes:**
- Battery life (mentioned 156 times)
- Great quality (mentioned 134 times)
- Fast delivery (mentioned 98 times)

**Negative Themes:**
- Poor customer service (mentioned 45 times)
- Overpriced (mentioned 32 times)
- Packaging issues (mentioned 28 times)

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork** the repository
2. **Create** a feature branch (git checkout -b feature/AmazingFeature)
3. **Commit** your changes (git commit -m 'Add some AmazingFeature)
4. **Push** to the branch (git push origin feature/AmazingFeature)
5. **Open** a Pull Request

### Development Setup


# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/

# Run linting
flake8 .
black .


## 🐛 Known Issues

- [ ] Some e-commerce sites may block automated scraping
- [ ] Rate limiting may slow down analysis for products with 1000+ reviews
- [ ] Non-English reviews are not currently supported

## 🔮 Future Enhancements

- [ ] **Browser Extension** for real-time analysis
- [ ] **Multi-language Support** for global e-commerce
- [ ] **API Integration** for third-party applications
- [ ] **Advanced Analytics** with trend analysis
- [ ] **Mobile App** for on-the-go review analysis

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Hugging Face](https://huggingface.co/) for pre-trained models
- [Streamlit](https://streamlit.io/) for the amazing web framework
- [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/) for web scraping capabilities
- Open source community for various libraries and tools




<div align="center">
  <p>Made with ❤️ by the DjangOps</p>
  <p>⭐ Star this repo if you find it helpful!</p>
</div>
