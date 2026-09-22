class ProgressTracker:

    def __init__(self):
        self.stage = "STARTING"
        self.message = "Starting analysis..."
        self.progress = 0

    def update(self, stage, message, progress):
        self.stage = stage
        self.message = message
        self.progress = progress

        print(
            f"[{progress:3}%] {stage}: {message}"
        )

    def get_status(self):
        return {
            "stage": self.stage,
            "message": self.message,
            "progress": self.progress
        }