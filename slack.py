from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import streamlit as st
from datetime import datetime

slack_token = st.secret["token"]
client = WebClient(token=slack_token)
slack_channel = "C087833T8K0"

def slack_send(msg):
    try:
        response = client.chat_postMessage(
            channel=slack_channel, #채널 id를 입력합니다.
            text=msg
        )
    except SlackApiError as e:
        assert e.response["error"]

# 파일 업로드하는 함수
def slack_upload(slack_file):
    try:
        result = client.files_upload_v2(file=slack_file, channel = slack_channel, title=f'data_{datetime.today()}')
    except:
        print("Error while saving")