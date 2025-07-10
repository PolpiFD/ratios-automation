import os, asyncio, logging, re
from datetime import datetime, timezone
import msal
import httpx
from azure.data import TableClient