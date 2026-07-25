from apscheduler.schedulers.blocking import BlockingScheduler    # runs the scheduler in the foreground
from apscheduler.triggers.cron import CronTrigger                # lets us define time-based schedules
from main import run                                             # imports our agent's main function
import logging                                                   # lets us log what the scheduler is doing

# sets up logging so we can see what's happening in the terminal
logging.basicConfig(
    level=logging.INFO,                                          # shows INFO level messages and above
    format="%(asctime)s - %(message)s"                          # shows timestamp with each message
)

def scheduled_run():
    # wrapper function that logs before and after each agent run
    logging.info("⏰ Scheduled run starting...")
    run()                                                        # calls your full agent pipeline
    logging.info("✅ Scheduled run complete. Next run tomorrow.")

# creates the scheduler instance
scheduler = BlockingScheduler()

# adds your agent as a scheduled job
scheduler.add_job(
    scheduled_run,                                               # the function to run
    CronTrigger(hour=2, minute=0),                              # runs every day at 2:00 AM
    id="veille_agent",                                           # unique name for this job
    name="Veille Scientifique daily run",                        # human readable name
    replace_existing=True                                        # replaces job if scheduler restarts
)

logging.info("📅 Scheduler started — agent will run every day at 2:00 AM")
logging.info("   Press Ctrl+C to stop")

try:
    scheduler.start()                                            # starts the scheduler — runs forever
except KeyboardInterrupt:
    logging.info("Scheduler stopped.")                           # handles Ctrl+C gracefully
    scheduler.shutdown()                                         # cleanly shuts down the scheduler