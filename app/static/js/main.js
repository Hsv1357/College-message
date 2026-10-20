/**
 * CampusConnect - Client-Side Interactive JavaScript
 */

document.addEventListener("DOMContentLoaded", function () {
  // 1. Password Visibility Toggle
  initPasswordToggles();

  // 2. Loading state on form submissions
  initFormLoadingStates();

  // 3. Dynamic role fields in Create Account form
  initRoleFieldVisibility();

  // 4. Edit User Modal population
  initEditUserModal();

  // 5. Sidebar Toggle for Mobile View
  initSidebarToggle();
});

/**
 * Handles toggling password input visibility between 'password' and 'text'.
 */
function initPasswordToggles() {
  const toggleButtons = document.querySelectorAll(".cc-password-toggle");
  toggleButtons.forEach((btn) => {
    btn.addEventListener("click", function () {
      const targetInputId = this.getAttribute("data-target");
      const input = document.getElementById(targetInputId);
      if (!input) return;

      const isPassword = input.getAttribute("type") === "password";
      input.setAttribute("type", isPassword ? "text" : "password");

      // Update button icon/label
      const icon = this.querySelector("i");
      if (icon) {
        if (isPassword) {
          icon.classList.remove("bi-eye");
          icon.classList.add("bi-eye-slash");
        } else {
          icon.classList.remove("bi-eye-slash");
          icon.classList.add("bi-eye");
        }
      }
      this.setAttribute("aria-label", isPassword ? "Hide password" : "Show password");
    });
  });
}

/**
 * Attaches loading spinners to submit buttons on form submit.
 */
function initFormLoadingStates() {
  const forms = document.querySelectorAll("form.cc-loading-form");
  forms.forEach((form) => {
    form.addEventListener("submit", function () {
      const submitBtn = this.querySelector("button[type='submit']");
      if (submitBtn) {
        submitBtn.disabled = true;
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = `
          <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
          Processing...
        `;
        // Safety timeout to re-enable in case form is halted by browser validation
        setTimeout(() => {
          if (submitBtn.disabled && !document.hidden) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
          }
        }, 12000);
      }
    });
  });
}

/**
 * Adjusts visible form sections based on selected Role in Create Account form.
 */
function initRoleFieldVisibility() {
  const roleSelect = document.getElementById("accountRoleSelect");
  if (!roleSelect) return;

  const studentFields = document.querySelectorAll(".role-field-student");
  const staffFields = document.querySelectorAll(".role-field-staff");
  const parentFields = document.querySelectorAll(".role-field-parent");

  function updateVisibility() {
    const selectedRole = roleSelect.value;

    studentFields.forEach((el) => {
      el.style.display = selectedRole === "student" ? "block" : "none";
    });
    staffFields.forEach((el) => {
      el.style.display = selectedRole === "staff" ? "block" : "none";
    });
    parentFields.forEach((el) => {
      el.style.display = selectedRole === "parent" ? "block" : "none";
    });
  }

  roleSelect.addEventListener("change", updateVisibility);
  updateVisibility(); // Initialize on page load
}

/**
 * Populates Edit User modal when triggered.
 */
function initEditUserModal() {
  const editModal = document.getElementById("editUserModal");
  if (!editModal) return;

  editModal.addEventListener("show.bs.modal", function (event) {
    const button = event.relatedTarget;
    if (!button) return;

    const uid = button.getAttribute("data-uid");
    const userId = button.getAttribute("data-userid");
    const fullName = button.getAttribute("data-fullname");
    const email = button.getAttribute("data-email");
    const phone = button.getAttribute("data-phone");
    const department = button.getAttribute("data-department");
    const className = button.getAttribute("data-classname");
    const parentStudentIds = button.getAttribute("data-parentstudentids");

    const form = editModal.querySelector("#editUserForm");
    if (form) {
      form.action = `/admin/users/${uid}/edit`;
    }

    const modalUserId = editModal.querySelector("#modalUserId");
    if (modalUserId) modalUserId.textContent = userId || uid;

    const modalFullNameInput = editModal.querySelector("#modalFullName");
    if (modalFullNameInput) modalFullNameInput.value = fullName || "";

    const modalEmailInput = editModal.querySelector("#modalEmail");
    if (modalEmailInput) modalEmailInput.value = email || "";

    const modalPhoneInput = editModal.querySelector("#modalPhone");
    if (modalPhoneInput) modalPhoneInput.value = phone || "";

    const modalDeptInput = editModal.querySelector("#modalDepartment");
    if (modalDeptInput) modalDeptInput.value = department || "";

    const modalClassInput = editModal.querySelector("#modalClassName");
    if (modalClassInput) modalClassInput.value = className || "";

    const modalParentIdsInput = editModal.querySelector("#modalParentStudentIds");
    if (modalParentIdsInput) modalParentIdsInput.value = parentStudentIds || "";
  });
}

/**
 * Toggles sidebar visibility on mobile devices.
 */
function initSidebarToggle() {
  const sidebarToggleBtn = document.getElementById("sidebarToggleBtn");
  const sidebar = document.querySelector(".cc-sidebar");
  if (!sidebarToggleBtn || !sidebar) return;

  sidebarToggleBtn.addEventListener("click", function () {
    sidebar.classList.toggle("open");
  });
}
