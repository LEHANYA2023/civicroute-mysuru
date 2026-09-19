from datetime import datetime

from issue_classifier import classify_issue
from jurisdiction_engine import determine_jurisdiction
from routing_engine import calculate_priority, build_route

print("Classifier:", classify_issue("pothole.jpg", "Large pothole on road"))
print("Jurisdiction:", determine_jurisdiction("Vijayanagar", "Pothole", datetime.now()))
print("Priority:", calculate_priority("Pothole", "Large pothole causing danger"))
print("Route:", build_route(
    "Vijayanagar",
    "Pothole",
    "Large pothole causing danger",
    "pothole.jpg",
    datetime.now(),
    check_duplicate=False,
))
print("Backend logic test completed.")

