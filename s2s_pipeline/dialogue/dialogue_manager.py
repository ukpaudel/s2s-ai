# Dialogue manager placeholder
class DialogueManager:
    def __init__(self):
        self.history = []
        self.state = {}
    
    def update_state(self, user_input, llm_response, confidence=None):
        self.history.append({
            "user": user_input,
            "assistant": llm_response,
            "confidence": confidence
        })
    
    def get_context_snippet(self):
        return "\n".join([f"User: {h['user']} | Assistant: {h['assistant']}" for h in self.history[-3:]])
