class ChatwootClient:
    def __init__(self, base_url: str, api_token: str):
        self.base_url = base_url
        self.headers = {'Authorization': f'Bearer {api_token}'}

    def send_message(self, conversation_id: int, message: str):
        # Implementação básica
        pass
