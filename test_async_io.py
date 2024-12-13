# use async IO to call shell command
import asyncio

async def run_command(command):
    """
    Asynchronously run a command and return its output.

    :param command: The command to execute as a list of strings.
    :return: The standard output and standard error of the command.
    """
    print(f"[DEBUG] Starting command: {' '.join(command)}")
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    print("[DEBUG] Process started, waiting for completion...")
    # Wait for the command to complete
    stdout, stderr = await process.communicate()

    print("[DEBUG] Process completed.")
    print(f"[DEBUG] STDOUT: {stdout.decode()[:100]}...")  # Preview first 100 characters
    print(f"[DEBUG] STDERR: {stderr.decode()[:100]}...")  # Preview first 100 characters

    return stdout.decode(), stderr.decode()

if __name__ == "__main__":
    import time

    # The command to execute (as a list of strings)
    # /hadoop/spark-2.4.5-bin-hadoop2.7/bin/spark-submit --class MovieLensALS /hadoop/Spark_Recommend-1.0-SNAPSHOT.jar /hadoop/movie_recommend/ /hadoop/movie_recommend/personalRatings.dat 10 5 10
    command = ["/hadoop/spark-2.4.5-bin-hadoop2.7/bin/spark-submit", "--class" ,"MovieLensALS",
                "/hadoop/Spark_Recommend-1.0-SNAPSHOT.jar","/hadoop/movie_recommend/",
                "/hadoop/movie_recommend/personalRatings.dat","10", "5", "10"]

    print(f"[DEBUG] Command to run: {command}")
    start_time = time.time()

    # Run the command synchronously (blocking)
    output, error = asyncio.run(run_command(command))

    elapsed_time = time.time() - start_time

    print("[DEBUG] Command execution completed.")
    print(f"[DEBUG] Elapsed Time: {elapsed_time:.2f} seconds")

    # Print the output and elapsed time
    print("Output:")
    print(output)
    print("Error:")
    print(error)
    print(f"Elapsed Time: {elapsed_time:.2f} seconds")