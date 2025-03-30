from setuptools import setup, find_packages

setup(
    name="PyTradeAnalytics",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "numpy",
        "plotly",
        "dash",
        "dash-bootstrap-components",
        "flask",
        "flask-cors>=3.0.10",  # Specify minimum version to avoid the broken version
        "yfinance",
        "nsepython",
        "beautifulsoup4",
        "requests",
        "pandas-ta",
        "ta",
    ],
    python_requires='>=3.7',
    author="PyTrade Development Team",
    author_email="example@example.com",
    description="Analytics tools for trading and market analysis",
    keywords="finance, trading, analytics, stock market",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Financial and Insurance Industry",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
)
