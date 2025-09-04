import logging
import random
import time
from collections.abc import Callable

logger = logging.getLogger(__name__)


def retry_with_backoff(
    func: Callable,
    max_retries: int = 10,
    backoff_factor: float = 2,
    max_backoff: float = 60,
    jitter_range: tuple = (1, 5),
    retry_status_codes: list[int] | None = None,
    exclude_status_codes: list[int] | None = None,
    timeout: float | None = None,
):
    """
    Retry a function with exponential backoff, jitter, and an optional timeout.

    Args:
        func (Callable): The function to retry. It should return an HTTP response-like object with a `status_code` attribute.
        max_retries (int): Maximum number of retries. Default is 10.
        backoff_factor (float): Initial backoff duration in seconds. Default is 2.
        max_backoff (float): Maximum backoff time in seconds. Default is 60.
        jitter_range (tuple): Range for jitter (min, max) in seconds. Default is (1, 5).
        retry_status_codes (Optional[List[int]]): List of HTTP status codes to retry on.
        exclude_status_codes (Optional[List[int]]): List of HTTP status codes to exclude from retrying. If provided, these will not be retried.
        timeout (Optional[float]): Total time allowed for retries in seconds. If None, there is no timeout. Default is None.

    Returns:
        The return value of the function, if successful.

    Raises:
        TimeoutError: If the total retry time exceeds the timeout.
        Exception: The last exception raised if all retries fail.
    """
    retries = 0
    start_time = time.time()
    status_code = None

    while retries < max_retries:
        try:
            response = func()
            status_code = getattr(response, "status_code", None)

            # Check if retry is needed based on status codes
            if retry_status_codes and status_code not in retry_status_codes:
                return response
            if exclude_status_codes and status_code in exclude_status_codes:
                return response

        except Exception as e:
            if retries == max_retries - 1:
                raise e  # Re-raise last exception
            logger.warning(
                f"[Retry Function] Error in function {func.__name__}. Retrying... Count: {retries + 1}; Error: {e}"
            )

        # Calculate backoff time with jitter
        backoff_time = min(backoff_factor * (2 ** retries), max_backoff)
        jitter = random.uniform(*jitter_range)
        total_backoff_time = backoff_time + jitter

        # Check timeout
        elapsed_time = time.time() - start_time
        if timeout and elapsed_time + total_backoff_time > timeout:
            raise TimeoutError(
                f"Retry operation timed out after {timeout} seconds. Status: {status_code}"
            )

        time.sleep(total_backoff_time)
        retries += 1

    logger.error(
        f"[Retry Function] Error in function {func.__name__}. Exceeded max retries ({max_retries}) without success."
    )
    raise Exception(
        f"[Retry Function] Exceeded max retries ({max_retries}) without success. Status: {status_code}"
    )
