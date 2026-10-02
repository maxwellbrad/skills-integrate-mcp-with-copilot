document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");
  const loginForm = document.getElementById("login-form");
  const sessionPanel = document.getElementById("session-panel");
  const sessionIdentity = document.getElementById("session-identity");
  const authMessage = document.getElementById("auth-message");
  const emailGroup = document.getElementById("email-group");
  const emailInput = document.getElementById("email");
  const signinRequired = document.getElementById("signin-required");
  let currentUser = null;

  function updateAuthUI() {
    const signedIn = Boolean(currentUser);
    loginForm.classList.toggle("hidden", signedIn);
    sessionPanel.classList.toggle("hidden", !signedIn);
    signupForm.classList.toggle("hidden", !signedIn);
    signinRequired.classList.toggle("hidden", signedIn);
    emailGroup.classList.toggle("hidden", currentUser?.role !== "staff");
    emailInput.required = currentUser?.role === "staff";
    if (currentUser) {
      sessionIdentity.textContent = `${currentUser.email} (${currentUser.role})`;
    }
  }

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message
      activitiesList.innerHTML = "";
      while (activitySelect.options.length > 1) {
        activitySelect.remove(1);
      }

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft =
          details.max_participants - details.participants.length;

        // Create participants HTML with delete icons instead of bullet points
        const participantsHTML =
          details.participants.length > 0
            ? `<div class="participants-section">
              <h5>Participants:</h5>
              <ul class="participants-list">
                ${details.participants
                  .map((email) => {
                    const canUnregister =
                      currentUser &&
                      (currentUser.role === "staff" ||
                        currentUser.email.toLowerCase() === email.toLowerCase());
                    const unregisterButton = canUnregister
                      ? `<button class="delete-btn" data-activity="${name}" data-email="${email}" aria-label="Unregister ${email}">Remove</button>`
                      : "";
                    return `<li><span class="participant-email">${email}</span>${unregisterButton}</li>`;
                  })
                  .join("")}
              </ul>
            </div>`
            : `<p><em>No participants yet</em></p>`;

        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          <div class="participants-container">
            ${participantsHTML}
          </div>
        `;

        activitiesList.appendChild(activityCard);

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });

      // Add event listeners to delete buttons
      document.querySelectorAll(".delete-btn").forEach((button) => {
        button.addEventListener("click", handleUnregister);
      });
    } catch (error) {
      activitiesList.innerHTML =
        "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle unregister functionality
  async function handleUnregister(event) {
    const button = event.target;
    const activity = button.getAttribute("data-activity");
    const email = button.getAttribute("data-email");

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(
          activity
        )}/unregister?email=${encodeURIComponent(email)}`,
        {
          method: "DELETE",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";

        // Refresh activities list to show updated participants
        fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to unregister. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error unregistering:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const activity = document.getElementById("activity").value;
    const email = emailInput.value.trim();
    const emailQuery = currentUser.role === "staff" ? `?email=${encodeURIComponent(email)}` : "";

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(
          activity
        )}/signup${emailQuery}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";
        signupForm.reset();

        // Refresh activities list to show updated participants
        fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    authMessage.classList.add("hidden");
    try {
      const response = await fetch("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: document.getElementById("login-email").value,
          password: document.getElementById("login-password").value,
        }),
      });
      const result = await response.json();
      if (!response.ok) {
        throw new Error(result.detail || "Sign in failed");
      }
      currentUser = result;
      loginForm.reset();
      updateAuthUI();
      await fetchActivities();
    } catch (error) {
      authMessage.textContent = error.message || "Failed to sign in";
      authMessage.className = "error";
      authMessage.classList.remove("hidden");
    }
  });

  document.getElementById("logout-button").addEventListener("click", async () => {
    await fetch("/auth/logout", { method: "POST" });
    currentUser = null;
    updateAuthUI();
    await fetchActivities();
  });

  async function initialize() {
    const response = await fetch("/auth/me");
    currentUser = response.ok ? await response.json() : null;
    updateAuthUI();
    await fetchActivities();
  }

  initialize();
});
