const state = {
  user: null,
  workouts: [],
  notifications: [],
  exercises: [],
  workoutExercises: [],
  progressSummary: null,
  weeklyVolume: [],
  exerciseRecords: [],
  templates: [],
  goals: [],
  trainerUsers: [],
  unreadCount: 0,
  workoutFilter: "all",
};

const tokenKey = "stride_access_token";
const refreshKey = "stride_refresh_token";
const $ = (selector) => document.querySelector(selector);

function setTokens(accessToken, refreshToken) {
  localStorage.setItem(tokenKey, accessToken);
  localStorage.setItem(refreshKey, refreshToken);
}

function clearTokens() {
  localStorage.removeItem(tokenKey);
  localStorage.removeItem(refreshKey);
}

function getToken() {
  return localStorage.getItem(tokenKey);
}

function iconRefresh() {
  window.lucide?.createIcons();
}

function toast(message) {
  const element = $("#toast");
  element.textContent = message;
  element.hidden = false;
  window.clearTimeout(toast.timeout);
  toast.timeout = window.setTimeout(() => {
    element.hidden = true;
  }, 3600);
}

function apiErrorMessage(payload) {
  if (Array.isArray(payload.detail)) {
    return payload.detail
      .map((item) => item.msg || "Некорректные данные")
      .join(". ");
  }

  return payload.detail || "Не удалось выполнить запрос.";
}

async function api(path, options = {}, canRefresh = true) {
  const headers = new Headers(options.headers || {});
  const token = getToken();

  if (token && options.auth !== false) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(path, { ...options, headers });

  if (response.status === 401 && canRefresh && localStorage.getItem(refreshKey)) {
    const refreshed = await refreshSession();
    if (refreshed) {
      return api(path, options, false);
    }
  }

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(apiErrorMessage(payload));
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

async function refreshSession() {
  const refreshToken = localStorage.getItem(refreshKey);
  if (!refreshToken) return false;

  try {
    const data = await api("/auth/refresh", {
      method: "POST",
      auth: false,
      body: JSON.stringify({ refresh_token: refreshToken }),
    }, false);
    setTokens(data.access_token, data.refresh_token);
    return true;
  } catch {
    signOut();
    return false;
  }
}

function formatDate(value, options = { day: "numeric", month: "short" }) {
  return new Intl.DateTimeFormat("ru-RU", options).format(new Date(value));
}

function formatTime(value) {
  return new Intl.DateTimeFormat("ru-RU", { hour: "2-digit", minute: "2-digit" }).format(new Date(value));
}

function formatNumber(value) {
  return new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 1 }).format(value || 0);
}

function toLocalInputValue(value = new Date()) {
  const date = new Date(value);
  const offsetDate = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  return offsetDate.toISOString().slice(0, 16);
}

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function statusClass(status) {
  if (status === "сделано") return "done";
  if (status === "пропущено") return "missed";
  return "planned";
}

function workoutStatus(status) {
  if (status === "сделано") return "Завершена";
  if (status === "пропущено") return "Пропущена";
  return "Запланирована";
}

function emptyState(title, subtitle, iconName = "calendar-plus") {
  const box = element("div", "empty-state");
  const icon = document.createElement("i");
  icon.dataset.lucide = iconName;
  box.append(icon, element("strong", "", title), element("span", "", subtitle));
  return box;
}

function renderWorkoutList(target, workouts) {
  target.replaceChildren();
  if (!workouts.length) {
    target.append(emptyState("Пока ничего нет", "Добавь тренировку, чтобы увидеть ее здесь."));
    iconRefresh();
    return;
  }

  workouts.forEach((workout) => {
    const date = new Date(workout.planned_at);
    const row = element("article", "workout-row");
    const day = element("div", "workout-day");
    day.append(element("strong", "", String(date.getDate())), element("span", "", formatDate(date, { month: "short" }).replace(".", "")));

    const info = element("div", "workout-info");
    info.append(element("h3", "", workout.title), element("p", "", `${formatDate(date, { weekday: "long", day: "numeric", month: "long" })}, ${formatTime(date)}`));

    const actions = element("div", "workout-actions");
    actions.append(element("span", `status-chip ${statusClass(workout.status)}`, workoutStatus(workout.status)));
    if (workout.status !== "сделано") {
      const done = element("button", "icon-button");
      done.dataset.action = "open-complete-workout";
      done.dataset.id = workout.id;
      done.title = "Заполнить дневник";
      done.ariaLabel = "Заполнить дневник тренировки";
      const doneIcon = document.createElement("i");
      doneIcon.dataset.lucide = "check";
      done.append(doneIcon);
      actions.append(done);
    }
    const build = element("button", "icon-button");
    build.dataset.action = "open-builder";
    build.dataset.id = workout.id;
    build.title = "Собрать упражнения";
    build.ariaLabel = "Собрать упражнения";
    const buildIcon = document.createElement("i");
    buildIcon.dataset.lucide = "list-plus";
    build.append(buildIcon);
    actions.append(build);
    if (workout.status === "запланировано") {
      const missed = element("button", "icon-button");
      missed.dataset.action = "miss-workout";
      missed.dataset.id = workout.id;
      missed.title = "Отметить пропущенной";
      missed.ariaLabel = "Отметить пропущенной";
      const missedIcon = document.createElement("i");
      missedIcon.dataset.lucide = "calendar-x";
      missed.append(missedIcon);
      actions.append(missed);
    }
    const remove = element("button", "icon-button");
    remove.dataset.action = "delete-workout";
    remove.dataset.id = workout.id;
    remove.title = "Удалить тренировку";
    remove.ariaLabel = "Удалить тренировку";
    const removeIcon = document.createElement("i");
    removeIcon.dataset.lucide = "trash-2";
    remove.append(removeIcon);
    actions.append(remove);
    row.append(day, info, actions);
    target.append(row);
  });
  iconRefresh();
}

function renderDashboard() {
  const planned = state.workouts.filter((workout) => workout.status !== "сделано");
  const completed = state.workouts.filter((workout) => workout.status === "сделано");
  const next = planned[0];

  $("#planned-count").textContent = planned.length;
  $("#completed-count").textContent = completed.length;
  $("#unread-count").textContent = state.unreadCount;

  if (next) {
    $("#next-workout-title").textContent = next.title;
    $("#next-workout-time").textContent = `${formatDate(next.planned_at, { weekday: "long", day: "numeric", month: "long" })} в ${formatTime(next.planned_at)}`;
    $("#next-workout-action").textContent = "Открыть план";
    $("#next-workout-action").dataset.view = "plan";
    delete $("#next-workout-action").dataset.openDialog;
  } else {
    $("#next-workout-title").textContent = "Добавь первую тренировку";
    $("#next-workout-time").textContent = "Собери план на неделю и начни с одного шага.";
    $("#next-workout-action").textContent = "Запланировать";
    $("#next-workout-action").dataset.openDialog = "workout-dialog";
    delete $("#next-workout-action").dataset.view;
  }
  renderWorkoutList($("#dashboard-workouts"), planned);
  iconRefresh();
}

function renderPlan() {
  const filtered = state.workoutFilter === "all"
    ? state.workouts
    : state.workouts.filter((workout) => workout.status === state.workoutFilter);
  renderWorkoutList($("#plan-workouts"), filtered);
}

function renderProgress() {
  const summary = state.progressSummary || {};
  $("#progress-weekly-volume").textContent = formatNumber(summary.weekly_volume);
  $("#progress-weekly-workouts").textContent = summary.completed_this_week || 0;
  $("#progress-streak").textContent = summary.current_streak_weeks || 0;
  $("#progress-best").textContent = summary.best_exercise_name || "-";

  const chart = $("#weekly-volume-chart");
  chart.replaceChildren();
  if (!state.weeklyVolume.length) {
    chart.append(emptyState("Пока нет завершенных тренировок", "Закрой первую тренировку, и график появится здесь.", "trending-up"));
  } else {
    const maxVolume = Math.max(...state.weeklyVolume.map((item) => item.volume), 1);
    state.weeklyVolume.slice(-8).forEach((item) => {
      const bar = element("article", "volume-bar");
      const fill = element("div", "volume-fill");
      fill.style.height = `${Math.max(8, (item.volume / maxVolume) * 100)}%`;
      const label = element("span", "", formatDate(item.week_start, { day: "numeric", month: "short" }).replace(".", ""));
      const value = element("strong", "", formatNumber(item.volume));
      bar.append(value, fill, label);
      chart.append(bar);
    });
  }

  const records = $("#records-grid");
  records.replaceChildren();
  if (!state.exerciseRecords.length) {
    records.append(emptyState("Рекордов пока нет", "Они появятся после завершения упражнений с весом или повторениями.", "trophy"));
  } else {
    state.exerciseRecords.forEach((record) => {
      const card = element("article", "record-card");
      card.append(element("h3", "", record.exercise_name));
      const stats = element("div", "record-stats");
      stats.append(
        element("span", "", `Вес: ${record.max_weight === null ? "-" : `${formatNumber(record.max_weight)} кг`}`),
        element("span", "", `Объем: ${formatNumber(record.max_volume)}`),
        element("span", "", `Подход: ${record.best_set_reps || 0} повт.`),
      );
      card.append(stats);
      records.append(card);
    });
  }
  iconRefresh();
}

function renderCalendar() {
  const target = $("#calendar-grid");
  target.replaceChildren();
  const byDate = new Map();
  state.workouts.forEach((workout) => {
    const key = new Date(workout.planned_at).toISOString().slice(0, 10);
    byDate.set(key, [...(byDate.get(key) || []), workout]);
  });
  const today = new Date();
  const start = new Date(today);
  start.setDate(today.getDate() - today.getDay() + 1);
  for (let i = 0; i < 28; i += 1) {
    const date = new Date(start);
    date.setDate(start.getDate() + i);
    const key = date.toISOString().slice(0, 10);
    const cell = element("article", "calendar-cell");
    cell.append(element("strong", "", formatDate(date, { day: "numeric", month: "short" }).replace(".", "")));
    (byDate.get(key) || []).forEach((workout) => {
      cell.append(element("span", `calendar-pill ${statusClass(workout.status)}`, workout.title));
    });
    target.append(cell);
  }
}

function renderGoals() {
  const target = $("#goals-grid");
  target.replaceChildren();
  if (!state.goals.length) {
    target.append(emptyState("Целей пока нет", "Добавь измеримую цель, чтобы держать фокус.", "target"));
    iconRefresh();
    return;
  }
  state.goals.forEach((goal) => {
    const card = element("article", "record-card");
    const progress = Math.min(100, Math.round((goal.current_value / goal.target_value) * 100));
    card.append(element("h3", "", goal.title));
    card.append(element("p", "muted", `${formatNumber(goal.current_value)} / ${formatNumber(goal.target_value)} ${goal.metric}`));
    const bar = element("div", "goal-bar");
    const fill = element("span", "");
    fill.style.width = `${progress}%`;
    bar.append(fill);
    card.append(bar);
    const actions = element("div", "card-actions");
    actions.append(goalAction(goal.id, "goal-progress", "plus", "Добавить прогресс"), goalAction(goal.id, "delete-goal", "trash-2", "Удалить"));
    card.append(actions);
    target.append(card);
  });
  iconRefresh();
}

function goalAction(id, action, iconName, title) {
  const button = element("button", "icon-button");
  button.dataset.action = action;
  button.dataset.id = id;
  button.title = title;
  button.ariaLabel = title;
  const icon = document.createElement("i");
  icon.dataset.lucide = iconName;
  button.append(icon);
  return button;
}

function renderTemplates() {
  const target = $("#templates-grid");
  target.replaceChildren();
  if (!state.templates.length) {
    target.append(emptyState("Шаблонов пока нет", "Создай шаблон из собранной тренировки.", "copy-check"));
    iconRefresh();
    return;
  }
  state.templates.forEach((template) => {
    const card = element("article", "record-card");
    card.append(element("h3", "", template.title));
    if (template.description) card.append(element("p", "muted", template.description));
    const actions = element("div", "card-actions");
    actions.append(goalAction(template.id, "schedule-template", "calendar-plus", "Запланировать"), goalAction(template.id, "delete-template", "trash-2", "Удалить"));
    card.append(actions);
    target.append(card);
  });
  iconRefresh();
}

function renderTrainer() {
  const target = $("#trainer-users");
  target.replaceChildren();
  if (!state.trainerUsers.length) {
    target.append(emptyState("Клиентов пока нет", "Пользователи появятся здесь для тренера или администратора.", "users"));
    iconRefresh();
    return;
  }
  state.trainerUsers.forEach((user) => {
    const row = element("article", "workout-row");
    row.append(element("div", "workout-day", user.username.slice(0, 2).toUpperCase()));
    const info = element("div", "workout-info");
    info.append(element("h3", "", user.username), element("p", "", `${user.email} · ${user.role}`));
    row.append(info);
    target.append(row);
  });
}

function renderExercises() {
  const target = $("#exercise-grid");
  target.replaceChildren();
  if (!state.exercises.length) {
    target.append(emptyState("Библиотека пока пуста", "Тренер или администратор может добавить упражнение.", "dumbbell"));
    iconRefresh();
    return;
  }

  state.exercises.forEach((exercise) => {
    const card = element("article", "exercise-card");
    if (exercise.muscle_image_url) {
      const image = document.createElement("img");
      image.className = "exercise-photo";
      image.src = exercise.muscle_image_url;
      image.alt = exercise.name;
      card.append(image);
    } else {
      const iconBox = element("span", "exercise-icon");
      const icon = document.createElement("i");
      icon.dataset.lucide = exercise.train === "кардио" ? "activity" : exercise.train === "растяжка" ? "move" : "dumbbell";
      iconBox.append(icon);
      card.append(iconBox);
    }
    const content = element("div", "exercise-content");
    content.append(element("h3", "", exercise.name));
    if (exercise.description) content.append(element("p", "", exercise.description));
    const meta = element("div", "exercise-meta");
    meta.append(element("span", "", exercise.train.replaceAll("_", " ")));
    if (exercise.muscle) meta.append(element("span", "", exercise.muscle.replaceAll("_", " ")));
    content.append(meta);
    const actions = element("div", "card-actions");
    const history = element("button", "icon-button");
    history.dataset.action = "exercise-history";
    history.dataset.id = exercise.id;
    history.title = "История упражнения";
    history.ariaLabel = "История упражнения";
    const historyIcon = document.createElement("i");
    historyIcon.dataset.lucide = "history";
    history.append(historyIcon);
    actions.append(history);
    content.append(actions);
    card.append(content);
    target.append(card);
  });
  iconRefresh();
}

function renderNotifications() {
  const target = $("#notification-list");
  target.replaceChildren();
  if (!state.notifications.length) {
    target.append(emptyState("Пока тихо", "Новые напоминания появятся здесь.", "bell"));
    iconRefresh();
    return;
  }

  state.notifications.forEach((notification) => {
    const item = element("article", `notification-item${notification.is_read ? "" : " unread"}`);
    item.append(element("h3", "", notification.title), element("p", "", notification.message));
    const date = element("time", "", formatDate(notification.created_at, { day: "numeric", month: "long", hour: "2-digit", minute: "2-digit" }));
    item.append(date);
    const action = element("button", "icon-button");
    action.dataset.action = notification.is_read ? "delete-notification" : "read-notification";
    action.dataset.id = notification.id;
    action.title = notification.is_read ? "Удалить уведомление" : "Отметить прочитанным";
    action.ariaLabel = action.title;
    const actionIcon = document.createElement("i");
    actionIcon.dataset.lucide = notification.is_read ? "trash-2" : "check";
    action.append(actionIcon);
    item.append(action);
    target.append(item);
  });
  iconRefresh();
}

async function loadExercises() {
  const params = new URLSearchParams();
  const train = $("#exercise-train-filter").value;
  const muscle = $("#exercise-muscle-filter").value;
  if (train) params.set("train_type", train);
  if (muscle) params.set("muscle", muscle);
  state.exercises = await api(`/exercises/${params.size ? `?${params.toString()}` : ""}`);
  renderExercises();
}

async function loadExerciseRecords() {
  const completedExerciseIds = [...new Set(
    state.workoutExercises
      .filter((link) => link.status === "сделано")
      .map((link) => link.exercise_id)
  )];
  const records = await Promise.all(
    completedExerciseIds.map((id) => api(`/progress/exercises/${id}`).catch(() => null))
  );
  state.exerciseRecords = records.filter(Boolean);
}

async function loadData() {
  const [user, workouts, notifications, unread, workoutExercises, progressSummary, weeklyVolume, templates, goals] = await Promise.all([
    api("/auth/me"),
    api("/workouts/?limit=100"),
    api("/notifications?limit=100"),
    api("/notifications/unread-count"),
    api("/workout-exercises/"),
    api("/progress/summary"),
    api("/progress/weekly-volume"),
    api("/templates/"),
    api("/goals/"),
  ]);
  state.user = user;
  state.workouts = workouts.sort((a, b) => new Date(a.planned_at) - new Date(b.planned_at));
  state.notifications = notifications;
  state.unreadCount = unread.unread_count;
  state.workoutExercises = workoutExercises;
  state.progressSummary = progressSummary;
  state.weeklyVolume = weeklyVolume;
  state.templates = templates;
  state.goals = goals;
  setUserDetails();
  await loadExercises();
  await loadExerciseRecords();
  if (["trainer", "admin"].includes(user.role)) {
    state.trainerUsers = await api("/admin/users/");
  } else {
    state.trainerUsers = [];
  }
  renderDashboard();
  renderPlan();
  renderCalendar();
  renderProgress();
  renderGoals();
  renderTemplates();
  renderTrainer();
  renderNotifications();
}

function setUserDetails() {
  const initials = state.user.username.slice(0, 2).toUpperCase();
  $("#profile-initials").textContent = initials;
  $("#profile-name").textContent = state.user.username;
  $("#greeting-name").textContent = state.user.username;
  $("#new-exercise-button").hidden = !["trainer", "admin"].includes(state.user.role);
  $("#trainer-nav").hidden = !["trainer", "admin"].includes(state.user.role);
  $("#notification-badge").hidden = state.unreadCount === 0;
  $("#notification-badge").textContent = state.unreadCount > 9 ? "9+" : state.unreadCount;
}

function showApp() {
  $("#auth-view").hidden = true;
  $("#app-view").hidden = false;
  iconRefresh();
}

function showAuth() {
  $("#auth-view").hidden = false;
  $("#app-view").hidden = true;
}

async function signIn(event) {
  event.preventDefault();
  const data = new FormData(event.currentTarget);
  try {
    const tokens = await api("/auth/login", { method: "POST", auth: false, body: JSON.stringify(Object.fromEntries(data)) });
    setTokens(tokens.access_token, tokens.refresh_token);
    await loadData();
    showApp();
    toast("Рады видеть тебя снова.");
  } catch (error) {
    toast(error.message);
  }
}

async function register(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const data = new FormData(form);
  const credentials = Object.fromEntries(data);
  try {
    await api("/auth/register", { method: "POST", auth: false, body: JSON.stringify(credentials) });
    const tokens = await api("/auth/login", { method: "POST", auth: false, body: JSON.stringify({
      username: credentials.username,
      password: credentials.password,
    }) });
    setTokens(tokens.access_token, tokens.refresh_token);
    form.reset();
    await loadData();
    showApp();
    toast("Аккаунт создан. Добро пожаловать.");
  } catch (error) {
    toast(error.message);
  }
}

function signOut() {
  clearTokens();
  state.user = null;
  $("#notification-drawer").hidden = true;
  $("#drawer-scrim").hidden = true;
  showAuth();
}

function setAuthMode(mode) {
  const isLogin = mode === "login";
  $("#login-form-wrap").hidden = !isLogin;
  $("#register-form-wrap").hidden = isLogin;
}

function setView(view) {
  document.querySelectorAll(".view").forEach((section) => {
    section.hidden = section.id !== `${view}-view`;
  });
  document.querySelectorAll(".nav-item[data-view]").forEach((button) => {
    button.classList.toggle("active", button.dataset.view === view);
  });
  $(".sidebar").classList.remove("open");
}

async function createWorkout(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const values = Object.fromEntries(new FormData(form));
  const payload = {
    title: values.title.trim(),
    planned_at: new Date(values.planned_at).toISOString(),
  };
  if (values.remind_at) payload.remind_at = new Date(values.remind_at).toISOString();
  try {
    await api("/workouts/", { method: "POST", body: JSON.stringify(payload) });
    form.reset();
    $("#workout-dialog").close();
    await loadData();
    toast("Тренировка запланирована.");
  } catch (error) {
    toast(error.message);
  }
}

function workoutLinks(workoutId) {
  return state.workoutExercises
    .filter((link) => link.workout_id === Number(workoutId))
    .sort((a, b) => a.order_index - b.order_index);
}

function exerciseName(exerciseId) {
  return state.exercises.find((item) => item.id === Number(exerciseId))?.name || `Упражнение #${exerciseId}`;
}

function openBuilder(workoutId) {
  const workout = state.workouts.find((item) => item.id === Number(workoutId));
  if (!workout) return;
  $("#builder-form").elements.workout_id.value = workout.id;
  $("#builder-title").textContent = workout.title;
  const select = $("#builder-exercise-select");
  select.replaceChildren();
  state.exercises.forEach((exercise) => {
    const option = document.createElement("option");
    option.value = exercise.id;
    option.textContent = exercise.name;
    select.append(option);
  });
  renderBuilderList(workout.id);
  $("#builder-dialog").showModal();
}

function renderBuilderList(workoutId) {
  const target = $("#builder-list");
  target.replaceChildren();
  const links = workoutLinks(workoutId);
  if (!links.length) {
    target.append(emptyState("Упражнения не выбраны", "Добавь первое упражнение выше.", "list-plus"));
    iconRefresh();
    return;
  }
  links.forEach((link, index) => {
    const row = element("article", "complete-row");
    row.append(element("h3", "", exerciseName(link.exercise_id)));
    row.append(element("p", "muted", `${link.sets}x${link.reps}${link.weight ? ` · ${formatNumber(link.weight)} кг` : ""}`));
    const actions = element("div", "card-actions");
    actions.append(builderButton(link, "builder-up", "arrow-up", "Выше"), builderButton(link, "builder-down", "arrow-down", "Ниже"), builderButton(link, "builder-remove", "trash-2", "Удалить"));
    if (index === 0) actions.firstChild.disabled = true;
    if (index === links.length - 1) actions.children[1].disabled = true;
    row.append(actions);
    target.append(row);
  });
  iconRefresh();
}

function builderButton(link, action, iconName, title) {
  const button = element("button", "icon-button");
  button.type = "button";
  button.dataset.action = action;
  button.dataset.workoutId = link.workout_id;
  button.dataset.exerciseId = link.exercise_id;
  button.title = title;
  button.ariaLabel = title;
  const icon = document.createElement("i");
  icon.dataset.lucide = iconName;
  button.append(icon);
  return button;
}

async function addBuilderExercise() {
  const workoutId = Number($("#builder-form").elements.workout_id.value);
  const links = workoutLinks(workoutId);
  const exerciseId = Number($("#builder-exercise-select").value);
  if (links.some((link) => link.exercise_id === exerciseId)) {
    toast("Это упражнение уже есть в тренировке.");
    return;
  }
  const workout = state.workouts.find((item) => item.id === workoutId);
  await api("/workout-exercises/", { method: "POST", body: JSON.stringify({
    workout_id: workoutId,
    exercise_id: exerciseId,
    order_index: links.length,
    sets: Number($("#builder-sets").value),
    reps: Number($("#builder-reps").value),
    weight: $("#builder-weight").value ? Number($("#builder-weight").value) : null,
    scheduled_at: workout.planned_at,
  }) });
  await loadData();
  openBuilder(workoutId);
}

async function createExercise(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const values = Object.fromEntries(new FormData(form));
  const payload = { ...values, name: values.name.trim() };
  if (!payload.muscle) payload.muscle = null;
  if (!payload.description) payload.description = null;
  try {
    await api("/exercises/", { method: "POST", body: JSON.stringify(payload) });
    form.reset();
    $("#exercise-dialog").close();
    await loadExercises();
    toast("Упражнение добавлено в библиотеку.");
  } catch (error) {
    toast(error.message);
  }
}

function openCompleteDialog(workoutId) {
  const workout = state.workouts.find((item) => item.id === Number(workoutId));
  if (!workout) return;

  const form = $("#complete-form");
  form.reset();
  form.elements.workout_id.value = workout.id;
  form.elements.completed_at.value = toLocalInputValue();
  $("#complete-title").textContent = workout.title;

  const target = $("#complete-exercises");
  target.replaceChildren();
  const links = state.workoutExercises
    .filter((link) => link.workout_id === workout.id)
    .sort((a, b) => a.order_index - b.order_index);

  if (!links.length) {
    target.append(emptyState("Упражнения не добавлены", "Тренировка будет завершена без дневника.", "check"));
  } else {
    links.forEach((link) => {
      const exercise = state.exercises.find((item) => item.id === link.exercise_id);
      const row = element("article", "complete-row");
      row.dataset.exerciseId = link.exercise_id;
      row.append(element("h3", "", exercise?.name || `Упражнение #${link.exercise_id}`));
      const fields = element("div", "complete-fields");
      fields.append(
        completeInput("sets", "Подходы", link.sets),
        completeInput("reps", "Повторы", link.reps),
        completeInput("weight", "Вес", link.weight ?? ""),
      );
      row.append(fields);
      const notes = element("label", "complete-notes", "Заметка");
      const textarea = document.createElement("textarea");
      textarea.name = "notes";
      textarea.rows = 2;
      textarea.maxLength = 1000;
      textarea.value = link.notes || "";
      notes.append(textarea);
      row.append(notes);
      target.append(row);
    });
  }

  $("#complete-dialog").showModal();
  iconRefresh();
}

function completeInput(name, label, value) {
  const wrapper = element("label", "", label);
  const input = document.createElement("input");
  input.name = name;
  input.type = "number";
  input.min = name === "weight" ? "0" : "1";
  input.step = name === "weight" ? "0.5" : "1";
  input.value = value;
  input.required = name !== "weight";
  wrapper.append(input);
  return wrapper;
}

async function completeWorkout(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const exercises = [...$("#complete-exercises").querySelectorAll(".complete-row")].map((row) => ({
    exercise_id: Number(row.dataset.exerciseId),
    sets: Number(row.querySelector('[name="sets"]').value),
    reps: Number(row.querySelector('[name="reps"]').value),
    weight: row.querySelector('[name="weight"]').value === "" ? null : Number(row.querySelector('[name="weight"]').value),
    notes: row.querySelector('[name="notes"]').value.trim() || null,
  }));
  const payload = {
    completed_at: new Date(form.elements.completed_at.value).toISOString(),
    exercises,
  };
  ["wellness_energy", "wellness_sleep", "wellness_soreness"].forEach((field) => {
    if (form.elements[field].value) payload[field] = Number(form.elements[field].value);
  });
  if (form.elements.completion_notes.value.trim()) payload.completion_notes = form.elements.completion_notes.value.trim();

  try {
    await api(`/workouts/${form.elements.workout_id.value}/complete`, { method: "POST", body: JSON.stringify(payload) });
    $("#complete-dialog").close();
    await loadData();
    toast("Тренировка сохранена в дневник.");
  } catch (error) {
    toast(error.message);
  }
}

async function createGoal(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const values = Object.fromEntries(new FormData(form));
  const payload = {
    title: values.title.trim(),
    metric: values.metric.trim(),
    current_value: Number(values.current_value || 0),
    target_value: Number(values.target_value),
  };
  if (values.deadline_at) payload.deadline_at = new Date(values.deadline_at).toISOString();
  try {
    await api("/goals/", { method: "POST", body: JSON.stringify(payload) });
    form.reset();
    $("#goal-dialog").close();
    await loadData();
    toast("Цель добавлена.");
  } catch (error) {
    toast(error.message);
  }
}

async function createTemplate(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const values = Object.fromEntries(new FormData(form));
  const links = workoutLinks(values.workout_id);
  const payload = {
    title: values.title.trim(),
    description: values.description.trim() || null,
    exercises: links.map((link) => ({
      exercise_id: link.exercise_id,
      order_index: link.order_index,
      sets: link.sets,
      reps: link.reps,
      weight: link.weight,
      notes: link.notes,
    })),
  };
  try {
    await api("/templates/", { method: "POST", body: JSON.stringify(payload) });
    form.reset();
    $("#template-dialog").close();
    await loadData();
    toast("Шаблон создан.");
  } catch (error) {
    toast(error.message);
  }
}

function fillTemplateWorkoutSelect() {
  const select = $("#template-form").elements.workout_id;
  select.replaceChildren();
  state.workouts.forEach((workout) => {
    const option = document.createElement("option");
    option.value = workout.id;
    option.textContent = workout.title;
    select.append(option);
  });
}

async function handleAction(button) {
  const id = button.dataset.id;
  try {
    if (button.dataset.action === "open-complete-workout") {
      openCompleteDialog(id);
    }
    if (button.dataset.action === "open-builder") {
      openBuilder(id);
    }
    if (button.dataset.action === "builder-add-exercise") {
      await addBuilderExercise();
    }
    if (button.dataset.action === "builder-remove") {
      await api(`/workout-exercises/${button.dataset.workoutId}/${button.dataset.exerciseId}`, { method: "DELETE" });
      await loadData();
      openBuilder(button.dataset.workoutId);
    }
    if (button.dataset.action === "builder-up" || button.dataset.action === "builder-down") {
      const links = workoutLinks(button.dataset.workoutId);
      const index = links.findIndex((link) => link.exercise_id === Number(button.dataset.exerciseId));
      const swapIndex = button.dataset.action === "builder-up" ? index - 1 : index + 1;
      if (swapIndex >= 0 && swapIndex < links.length) {
        const current = links[index];
        const other = links[swapIndex];
        await Promise.all([
          api(`/workout-exercises/${current.workout_id}/${current.exercise_id}`, { method: "PATCH", body: JSON.stringify({ order_index: other.order_index }) }),
          api(`/workout-exercises/${other.workout_id}/${other.exercise_id}`, { method: "PATCH", body: JSON.stringify({ order_index: current.order_index }) }),
        ]);
        await loadData();
        openBuilder(button.dataset.workoutId);
      }
    }
    if (button.dataset.action === "miss-workout") {
      await api(`/workouts/${id}`, { method: "PATCH", body: JSON.stringify({ status: "пропущено" }) });
      await loadData();
      toast("Тренировка отмечена пропущенной.");
    }
    if (button.dataset.action === "starter-plan") {
      await api("/workouts/starter-plan", { method: "POST" });
      await loadData();
      toast("Готовая неделя добавлена в план.");
    }
    if (button.dataset.action === "delete-workout") {
      if (!window.confirm("Удалить эту тренировку?")) return;
      await api(`/workouts/${id}`, { method: "DELETE" });
      await loadData();
      toast("Тренировка удалена.");
    }
    if (button.dataset.action === "read-notification") {
      await api(`/notifications/${id}/read`, { method: "PATCH" });
      await loadData();
    }
    if (button.dataset.action === "delete-notification") {
      await api(`/notifications/${id}`, { method: "DELETE" });
      await loadData();
      toast("Уведомление удалено.");
    }
    if (button.dataset.action === "goal-progress") {
      const goal = state.goals.find((item) => item.id === Number(id));
      const value = Number(window.prompt("Новое текущее значение", goal.current_value));
      if (!Number.isNaN(value)) {
        await api(`/goals/${id}`, { method: "PATCH", body: JSON.stringify({ current_value: value }) });
        await loadData();
      }
    }
    if (button.dataset.action === "delete-goal") {
      await api(`/goals/${id}`, { method: "DELETE" });
      await loadData();
      toast("Цель удалена.");
    }
    if (button.dataset.action === "schedule-template") {
      const value = window.prompt("Дата и время тренировки (YYYY-MM-DDTHH:mm)", toLocalInputValue());
      if (value) {
        await api(`/templates/${id}/workouts`, { method: "POST", body: JSON.stringify({ planned_at: new Date(value).toISOString() }) });
        await loadData();
        toast("Тренировка создана из шаблона.");
      }
    }
    if (button.dataset.action === "delete-template") {
      await api(`/templates/${id}`, { method: "DELETE" });
      await loadData();
      toast("Шаблон удален.");
    }
    if (button.dataset.action === "exercise-history") {
      const history = await api(`/progress/exercises/${id}/history`);
      if (!history.length) {
        toast("Истории по упражнению пока нет.");
        return;
      }
      window.alert(history.slice(0, 6).map((item) => (
        `${formatDate(item.completed_at, { day: "numeric", month: "short" })}: ${item.sets}x${item.reps}${item.weight ? `, ${formatNumber(item.weight)} кг` : ""}`
      )).join("\n"));
    }
  } catch (error) {
    toast(error.message);
  }
}

function setupHandlers() {
  $("#login-form").addEventListener("submit", signIn);
  $("#register-form").addEventListener("submit", register);
  $("#workout-form").addEventListener("submit", createWorkout);
  $("#complete-form").addEventListener("submit", completeWorkout);
  $("#goal-form").addEventListener("submit", createGoal);
  $("#template-form").addEventListener("submit", createTemplate);
  $("#exercise-form").addEventListener("submit", createExercise);
  $("#logout-button").addEventListener("click", signOut);
  $("#mobile-menu-button").addEventListener("click", () => $(".sidebar").classList.toggle("open"));
  $("#notifications-button").addEventListener("click", () => {
    $("#notification-drawer").hidden = false;
    $("#drawer-scrim").hidden = false;
  });
  [$("#close-notifications"), $("#drawer-scrim")].forEach((button) => button.addEventListener("click", () => {
    $("#notification-drawer").hidden = true;
    $("#drawer-scrim").hidden = true;
  }));
  [$("#exercise-train-filter"), $("#exercise-muscle-filter")].forEach((control) => control.addEventListener("change", () => loadExercises().catch((error) => toast(error.message))));

  document.addEventListener("click", (event) => {
    const authToggle = event.target.closest("[data-auth-mode]");
    if (authToggle) setAuthMode(authToggle.dataset.authMode);
    const dialogTrigger = event.target.closest("[data-open-dialog]");
    if (dialogTrigger) {
      if (dialogTrigger.dataset.openDialog === "template-dialog") fillTemplateWorkoutSelect();
      $("#" + dialogTrigger.dataset.openDialog).showModal();
    }
    const dialogCloser = event.target.closest("[data-close-dialog]");
    if (dialogCloser) $("#" + dialogCloser.dataset.closeDialog).close();
    const viewTrigger = event.target.closest("[data-view]");
    if (viewTrigger) setView(viewTrigger.dataset.view);
    const filter = event.target.closest("[data-workout-filter]");
    if (filter) {
      state.workoutFilter = filter.dataset.workoutFilter;
      document.querySelectorAll("[data-workout-filter]").forEach((button) => button.classList.toggle("active", button === filter));
      renderPlan();
    }
    const action = event.target.closest("[data-action]");
    if (action) handleAction(action);
  });
}

async function start() {
  const now = new Date();
  $("#today-label").textContent = new Intl.DateTimeFormat("ru-RU", { weekday: "long", day: "numeric", month: "long" }).format(now);
  setupHandlers();
  iconRefresh();
  if (!getToken()) return;
  try {
    await loadData();
    showApp();
  } catch (error) {
    clearTokens();
    showAuth();
    toast(error.message);
  }
}

start();
