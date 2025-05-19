# Dialogue manager placeholder
class DialogueManager:
    def __init__(self):
        self.history = []
        self.state = {}
        self.state = {"last_action": None, "completed_actions": set()}
    
    def update_state(self, user_input, llm_response, confidence=None,intent=None):
        self.history.append({
            "user": user_input,
            "assistant": llm_response,
            "confidence": confidence,
            "intent": intent
        })
    
    def get_context_snippet(self):
        return "\n".join([f"User: {h['user']} | Assistant: {h['assistant']}" for h in self.history[-3:]])
    
    def pop_last_turn(self):
        """Remove the most recent turn from history (used after a task finishes)."""
        if self.history:
            self.history.pop()
