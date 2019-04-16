# StockMonitor
This script fetches stock data, calculates RSI values and alarms via email if certain thresholds are exceeded. Thresholds can be configured per symbol.
## Howto
1. Download and install Python 3.7.x (https://www.python.org/downloads/)
2. Clone (or pull to update) this repository ```git clone https://github.com/molmutius/stockMonitor.git'```
3. Install dependencies
    ```
    python -m pip install--upgrade pip
    python -m pip install pandas
    python -m pip install pandas-datareader
    python -m pip install matplotlib
    ```
4. Adjust secrets, thresholds and email in ```config.ini```
5. Execute with ```python monitor.py```
6. If you need to run this on a regular basis, a good idea would be to configure a cron job. Example for daily execution at 5am:
    ```
    crontab -e
    0 5 * * * /usr/bin/python3 /path/to/stockMonitor/monitor.py >> ~/monitor.log 2>&1
    ```