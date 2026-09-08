import subprocess


class TaskHandler:

    def execute_command(self, args):
        command = args.get("command")

        if not command:
            raise ValueError("No command provided")

        try:
            result = subprocess.run(
                command.split(),
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                return {
                    "success": False,
                    "error": result.stderr.strip(),
                    "returncode": result.returncode,
                }

            return {
                "success": True,
                "output": result.stdout,
                "returncode": result.returncode,
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Command timed out",
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def list_directory(self, args):
        pass

    def upload_file(self, args):
        pass

    def write_file(self, args):
        pass

    def execute(self, task):
        task_type = task.get("task")
        args = task.get("args", {})

        handlers = {
            "command_execution": self.execute_command,
        }

        handler = handlers.get(task_type)

        if not handler:
            raise ValueError(f"Unknown task type: {task_type}")

        return handler(args)

task_manager = TaskHandler()