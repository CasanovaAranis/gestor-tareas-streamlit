import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
import json
import os
from werkzeug.security import generate_password_hash, check_password_hash

# --- Constantes y Configuración ---
DATA_DIR = "app_data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
WEEKLY_ENTRIES_FILE = os.path.join(DATA_DIR, "weekly_entries.json")
UNASSIGNED_TASKS_FILE = os.path.join(DATA_DIR, "unassigned_tasks.json")
VOTES_FILE = os.path.join(DATA_DIR, "votes.json")

TASK_STATUSES = ["Pendiente ⚪", "En Progreso 🟡", "Bloqueada 🔴", "Completada ✅"]
DEFAULT_INITIAL_PASSWORD = "changeme"
PROJECT_NAMES = ["Viruta 🪵", "Botillería 🍾", "Interno 🏠", "General ⚙️"] # NUEVO: Lista de Proyectos

# ... (Funciones de Manejo de Datos, Seguridad, initialize_data, get_current_week_year, new_password_setup_page, login_page, logout se mantienen igual que la versión anterior) ...
# COPIARÉ LAS FUNCIONES QUE NO CAMBIAN PARA TENER EL SCRIPT COMPLETO
# SI UNA FUNCIÓN CAMBIA, LO INDICARÉ.

# --- Funciones de Manejo de Datos (Persistencia) ---
def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def save_data(filepath, data):
    ensure_data_dir()
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_data(filepath, default_data_factory=dict):
    ensure_data_dir()
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            st.error(f"⚠️ Error al decodificar {filepath}. Se usarán datos por defecto. Considera revisar o eliminar el archivo si el problema persiste.")
            return default_data_factory()
    return default_data_factory()

# --- Funciones de Seguridad de Contraseñas ---
def hash_password(password):
    return generate_password_hash(password)

def check_password(hashed_password, password):
    if not hashed_password: 
        return False
    return check_password_hash(hashed_password, password)

# --- Configuración Inicial y Carga de Datos ---
def initialize_data():
    if 'initialized' not in st.session_state:
        st.session_state.users_db = load_data(USERS_FILE, dict)
        st.session_state.weekly_entries = load_data(WEEKLY_ENTRIES_FILE, dict)
        st.session_state.unassigned_tasks = load_data(UNASSIGNED_TASKS_FILE, list)
        st.session_state.votes = load_data(VOTES_FILE, dict)

        collaborator_names = {
            "tomas_c": "Tomas Casanova", "nicolas_c": "Nicolas Chavez",
            "vicente_h": "Vicente Hoya", "goli_t": "Goli Torres",
            "tomas_v": "Tomas Valenzuela", "fuad_h": "Fuad Hamed"
        }

        if not st.session_state.users_db:
            st.session_state.users_db = {
                "admin": {"password": hash_password(DEFAULT_INITIAL_PASSWORD), "role": "admin", "full_name": "Administrador", "password_set": False}
            }
            for username_key, full_name in collaborator_names.items():
                st.session_state.users_db[username_key] = {
                    "password": hash_password(DEFAULT_INITIAL_PASSWORD), "role": "collaborator",
                    "full_name": full_name, "password_set": False
                }
            save_data(USERS_FILE, st.session_state.users_db)
        else:
            users_updated = False
            for username, data in st.session_state.users_db.items():
                if "password_set" not in data:
                    data["password_set"] = False 
                    users_updated = True
                if "full_name" not in data:
                    data["full_name"] = collaborator_names.get(username, username.replace("_", " ").title()) if username != "admin" else "Administrador"
                    users_updated = True
            if users_updated:
                save_data(USERS_FILE, st.session_state.users_db)

        st.session_state.logged_in_user = None
        st.session_state.user_role = None
        st.session_state.user_full_name = None
        st.session_state.editing_task_id = None
        st.session_state.force_password_reset_for_user = None
        st.session_state.initialized = True


def get_current_week_year():
    return datetime.now().strftime("%Y-%V")

def new_password_setup_page(username):
    st.header(f"👋 ¡Hola, {st.session_state.users_db[username]['full_name']}!")
    st.subheader("Configura tu nueva contraseña")
    st.info("Por seguridad, es necesario que establezcas una nueva contraseña para tu cuenta.")

    with st.form("set_new_password_form"):
        new_password = st.text_input("Nueva Contraseña", type="password", key="new_pass_setup")
        confirm_password = st.text_input("Confirmar Nueva Contraseña", type="password", key="confirm_pass_setup")
        submitted = st.form_submit_button("Guardar Contraseña")

        if submitted:
            if not new_password or not confirm_password: st.error("Por favor, completa ambos campos.")
            elif new_password != confirm_password: st.error("Las contraseñas no coinciden.")
            elif len(new_password) < 6: st.error("La contraseña debe tener al menos 6 caracteres.")
            else:
                user_data = st.session_state.users_db[username]
                user_data["password"] = hash_password(new_password)
                user_data["password_set"] = True
                save_data(USERS_FILE, st.session_state.users_db)
                st.session_state.logged_in_user = username
                st.session_state.user_role = user_data["role"]
                st.session_state.user_full_name = user_data["full_name"]
                st.session_state.force_password_reset_for_user = None
                st.success("¡Contraseña actualizada exitosamente! Serás redirigido."); st.balloons(); st.rerun()

def login_page():
    st.header("🚀 Inicio de Sesión del Equipo")
    username = st.text_input("Usuario", key="login_user_main", placeholder="Ej: admin, tomas_c")
    password = st.text_input("Contraseña", type="password", key="login_pass_main")

    if st.button("Ingresar", key="login_button_main"):
        user_data = st.session_state.users_db.get(username)
        if user_data and check_password(user_data.get("password"), password):
            if not user_data.get("password_set", False):
                st.session_state.force_password_reset_for_user = username; st.rerun()
            else:
                st.session_state.logged_in_user = username
                st.session_state.user_role = user_data["role"]
                st.session_state.user_full_name = user_data.get("full_name", username)
                st.success(f"¡Bienvenido {st.session_state.user_full_name}!"); st.rerun()
        else: st.error("Usuario o contraseña incorrectos.")

def logout():
    keys_to_reset = ['logged_in_user', 'user_role', 'user_full_name', 'editing_task_id', 'force_password_reset_for_user']
    for key in keys_to_reset:
        if key in st.session_state: st.session_state[key] = None
    for key in list(st.session_state.keys()):
        if key.startswith("form_") or key in ["login_user_main", "login_pass_main", "main_menu_selection"]:
            del st.session_state[key]
    st.info("Has cerrado sesión."); st.rerun()

# --- MODIFICADO: weekly_input_page ---
def weekly_input_page():
    st.header(f"📝 Mi Plan Semanal - Semana {get_current_week_year()}")
    user = st.session_state.logged_in_user
    current_week = get_current_week_year()
    entry_key = f"{user}_{current_week}"

    current_entry = st.session_state.weekly_entries.get(entry_key, {'hours': 0, 'tasks': []})

    hours = st.number_input(
        "🕒 Horas que trabajarás esta semana:",
        min_value=0, max_value=100,
        value=current_entry.get('hours', 0),
        key=f"form_hours_{user}_{current_week}"
    )

    st.subheader("📋 Mis Tareas para esta Semana:")

    # Formulario para añadir/editar tarea
    if st.session_state.editing_task_id:
        task_to_edit_list = [t for t in current_entry.get('tasks', []) if t['id'] == st.session_state.editing_task_id]
        if task_to_edit_list:
            task_to_edit = task_to_edit_list[0]
            st.markdown(f"#### Editando Tarea: *{task_to_edit['title']}*")
            with st.form(key=f"form_edit_task_{task_to_edit['id']}", clear_on_submit=False):
                edited_title = st.text_input("Nuevo Título", value=task_to_edit['title'], key=f"edit_title_{task_to_edit['id']}")
                edited_desc = st.text_area("Nueva Descripción", value=task_to_edit['desc'], key=f"edit_desc_{task_to_edit['id']}")
                # NUEVO: Selector de proyecto en edición
                default_project_index = PROJECT_NAMES.index(task_to_edit.get("project", PROJECT_NAMES[0])) if task_to_edit.get("project") in PROJECT_NAMES else 0
                edited_project = st.selectbox("Proyecto Asignado", PROJECT_NAMES, index=default_project_index, key=f"edit_project_{task_to_edit['id']}")

                col1_edit, col2_edit = st.columns(2)
                with col1_edit: submitted_edit = st.form_submit_button("💾 Guardar Cambios")
                with col2_edit: submitted_cancel_edit = st.form_submit_button("❌ Cancelar")

                if submitted_edit and edited_title:
                    task_to_edit['title'] = edited_title
                    task_to_edit['desc'] = edited_desc
                    task_to_edit['project'] = edited_project # Guardar proyecto
                    st.session_state.weekly_entries[entry_key] = current_entry
                    save_data(WEEKLY_ENTRIES_FILE, st.session_state.weekly_entries)
                    st.session_state.editing_task_id = None
                    st.success("Tarea actualizada."); st.rerun()
                if submitted_cancel_edit:
                    st.session_state.editing_task_id = None; st.rerun()
        else:
            st.session_state.editing_task_id = None; st.rerun()
    else:
        with st.form(key=f"form_new_task_{user}_{current_week}", clear_on_submit=True):
            task_title = st.text_input("Título de la tarea", key=f"form_task_title_{user}")
            task_desc = st.text_area("Descripción de la tarea", key=f"form_task_desc_{user}")
            # NUEVO: Selector de proyecto al añadir
            task_project = st.selectbox("Asignar a Proyecto", PROJECT_NAMES, key=f"form_task_project_{user}")
            submitted_task = st.form_submit_button("➕ Añadir Tarea")

            if submitted_task and task_title and task_project:
                new_task = {
                    'id': str(uuid.uuid4()), 'title': task_title, 'desc': task_desc,
                    'status': TASK_STATUSES[0], 'project': task_project # Añadir proyecto
                }
                if 'tasks' not in current_entry or not isinstance(current_entry['tasks'], list):
                    current_entry['tasks'] = []
                current_entry['tasks'].append(new_task)
                st.session_state.weekly_entries[entry_key] = current_entry
                save_data(WEEKLY_ENTRIES_FILE, st.session_state.weekly_entries)
                st.success(f"Tarea '{task_title}' añadida al proyecto '{task_project}'."); st.rerun()

    tasks_list = current_entry.get('tasks', [])
    if tasks_list:
        st.markdown("---")
        st.markdown("#### Tareas Planeadas:")
        for i, task in enumerate(tasks_list):
            task_id_key_prefix = f"task_{task['id']}"
            with st.container(border=True):
                col_title_proj, col_status, col_actions = st.columns([3, 2, 2])
                with col_title_proj:
                    st.markdown(f"##### {task['title']}")
                    # Mostrar proyecto
                    st.markdown(f"###### _Proyecto: {task.get('project', 'No asignado')}_")
                    st.caption(task['desc'] if task['desc'] else "Sin descripción")
                
                with col_status: # ... (resto del código de estado sin cambios)
                    current_status_index = TASK_STATUSES.index(task['status']) if task.get('status') in TASK_STATUSES else 0
                    new_status = st.selectbox(
                        "Estado", TASK_STATUSES, index=current_status_index,
                        key=f"{task_id_key_prefix}_status_select", label_visibility="collapsed"
                    )
                    if new_status != task.get('status'):
                        task['status'] = new_status
                        st.session_state.weekly_entries[entry_key] = current_entry
                        save_data(WEEKLY_ENTRIES_FILE, st.session_state.weekly_entries); st.rerun()
                with col_actions: # ... (resto del código de acciones sin cambios)
                    if not st.session_state.editing_task_id:
                        if st.button("✏️ Editar", key=f"{task_id_key_prefix}_edit_btn", type="secondary", use_container_width=True):
                            st.session_state.editing_task_id = task['id']; st.rerun()
                        if st.button("🗑️ Eliminar", key=f"{task_id_key_prefix}_delete_btn", type="primary", use_container_width=True):
                            current_entry['tasks'].pop(i)
                            st.session_state.weekly_entries[entry_key] = current_entry
                            save_data(WEEKLY_ENTRIES_FILE, st.session_state.weekly_entries); st.rerun(); break
    else: st.info("Aún no has añadido tareas para esta semana.")

    st.markdown("---")
    if st.button("💾 Guardar Plan Semanal General", key=f"form_save_plan_{user}_{current_week}_main", type="primary"):
        current_entry['hours'] = hours
        st.session_state.weekly_entries[entry_key] = current_entry
        save_data(WEEKLY_ENTRIES_FILE, st.session_state.weekly_entries)
        st.success("¡Plan semanal guardado exitosamente!"); st.balloons()


# --- MODIFICADO: team_hub_page ---
def team_hub_page():
    st.header(f"🤝 Hub del Equipo - Semana {get_current_week_year()}")
    current_week = get_current_week_year()
    
    active_entries_this_week = []
    for user_id, user_data_db in st.session_state.users_db.items():
        if user_data_db["role"] == "collaborator":
            entry_key = f"{user_id}_{current_week}"
            user_entry = st.session_state.weekly_entries.get(entry_key)
            if user_entry and (user_entry.get('hours', 0) > 0 or user_entry.get('tasks')): # Considerar si tienen horas O tareas
                active_entries_this_week.append({
                    "user_id": user_id, "full_name": user_data_db.get("full_name", user_id),
                    "hours": user_entry.get('hours', 0), "tasks": user_entry.get('tasks', [])
                })

    st.subheader("🚀 Resumen Semanal del Equipo")
    if active_entries_this_week:
        total_team_hours = sum(entry['hours'] for entry in active_entries_this_week)
        num_contributors = len(active_entries_this_week)
        avg_hours = total_team_hours / num_contributors if num_contributors > 0 else 0
        total_tasks = sum(len(entry['tasks']) for entry in active_entries_this_week)
        completed_tasks = sum(1 for entry in active_entries_this_week for task in entry['tasks'] if task.get('status') == TASK_STATUSES[3])

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("👥 Colaboradores Activos", f"{num_contributors}")
        col2.metric("⏰ Horas Totales Planificadas", f"{total_team_hours} hrs")
        col3.metric("📊 Promedio Horas/Colab.", f"{avg_hours:.1f} hrs")
        col4.metric("✅ Tareas Completadas (Total)", f"{completed_tasks} de {total_tasks}")
    else: st.info("Aún no hay datos de colaboradores para mostrar un resumen esta semana.")
    
    st.markdown("---"); st.subheader("👤 Detalles por Colaborador")
    if not active_entries_this_week: st.write("Esperando que los colaboradores ingresen sus planes semanales...")

    for entry_data in active_entries_this_week:
        user = entry_data["user_id"]
        full_name = entry_data["full_name"]
        user_hours = entry_data["hours"]
        user_tasks = entry_data["tasks"]
        num_tasks = len(user_tasks)
        num_completed = sum(1 for t in user_tasks if t.get('status') == TASK_STATUSES[3])
        progress = (num_completed / num_tasks * 100) if num_tasks > 0 else 0

        with st.expander(f"**{full_name}** - {user_hours} hrs planificadas ({num_tasks} tareas)"):
            col_detail_1, col_detail_2 = st.columns([1,2])
            with col_detail_1:
                st.metric("⏰ Horas Planificadas", f"{user_hours} hrs")
                if num_tasks > 0: st.metric("🎯 Progreso Tareas", f"{num_completed}/{num_tasks}"); st.progress(int(progress))
                else: st.caption("Sin tareas asignadas")
            with col_detail_2:
                st.markdown("##### Tareas:")
                if user_tasks:
                    for task_idx, task in enumerate(user_tasks):
                        st.markdown(f"- **{task['title']}** ({task.get('status', 'N/A')})")
                        st.caption(f"  _{task.get('project', 'Sin proyecto')}_: {task['desc']}") # Mostrar proyecto
                else: st.write("No hay tareas detalladas para esta semana.")

            # --- MODIFICACIÓN PARA VOTO ÚNICO ---
            if user != st.session_state.logged_in_user:
                vote_key = f"{st.session_state.logged_in_user}_{current_week}_{user}"
                current_vote_score = st.session_state.votes.get(vote_key)
                vote_options_map = {"⭐": 1, "⭐⭐": 2, "⭐⭐⭐": 3, "⭐⭐⭐⭐": 4, "⭐⭐⭐⭐⭐": 5}
                vote_labels = list(vote_options_map.keys())

                st.markdown("---")
                if current_vote_score is not None: # Si ya votó
                    # Encontrar la etiqueta del voto actual
                    current_vote_label = ""
                    for label, score_val in vote_options_map.items():
                        if score_val == current_vote_score:
                            current_vote_label = label
                            break
                    st.markdown(f"**Tu voto para {full_name} esta semana: {current_vote_label}**")
                    st.caption("El voto ya fue emitido y no se puede cambiar para esta semana.")
                else: # Si no ha votado
                    st.markdown(f"**Votar por el aporte de {full_name}:**")
                    vote_form_cols = st.columns([3,1])
                    with vote_form_cols[0]:
                        selected_vote_label = st.radio(
                            "Valora:", vote_labels, index=2, horizontal=True,
                            key=f"vote_radio_{user}_{current_week}_{st.session_state.logged_in_user}",
                            label_visibility="collapsed"
                        )
                    with vote_form_cols[1]:
                        if st.button(f"🗳️ Votar", key=f"vote_btn_{user}_{current_week}_{st.session_state.logged_in_user}"):
                            st.session_state.votes[vote_key] = vote_options_map[selected_vote_label]
                            save_data(VOTES_FILE, st.session_state.votes)
                            st.success(f"Voto para {full_name} registrado como '{selected_vote_label}'."); st.rerun()
            else: st.caption("Este es tu perfil, no puedes votarte a ti mismo.")


# --- MODIFICADO: unassigned_tasks_page ---
def unassigned_tasks_page():
    st.header("🎯 Tareas Libres")
    current_week = get_current_week_year()
    user = st.session_state.logged_in_user
    user_role = st.session_state.user_role

    if user_role == "admin":
        st.subheader("➕ Añadir Nueva Tarea Libre")
        with st.form("new_unassigned_task_form", clear_on_submit=True):
            task_title = st.text_input("Título de la tarea")
            task_desc = st.text_area("Descripción de la tarea")
            # NUEVO: Selector de proyecto para tareas libres
            task_project = st.selectbox("Asignar a Proyecto", PROJECT_NAMES, key="unassigned_task_project_admin")
            submit_button = st.form_submit_button("Añadir Tarea Libre")

            if submit_button and task_title and task_project:
                new_task = {
                    'id': str(uuid.uuid4()), 'title': task_title, 'desc': task_desc,
                    'added_by': st.session_state.user_full_name, 'week_added': current_week,
                    'status': TASK_STATUSES[0], 'project': task_project # Añadir proyecto
                }
                st.session_state.unassigned_tasks.append(new_task)
                save_data(UNASSIGNED_TASKS_FILE, st.session_state.unassigned_tasks)
                st.success(f"Tarea '{task_title}' añadida al proyecto '{task_project}'."); st.rerun()

    st.subheader("📋 Tareas Disponibles para Tomar")
    if not st.session_state.unassigned_tasks: st.info("No hay tareas libres disponibles."); return

    tasks_to_remove_indices = []
    for i, task in enumerate(st.session_state.unassigned_tasks):
        with st.container(border=True):
            st.markdown(f"#### {task['title']}")
            # Mostrar proyecto de tarea libre
            st.markdown(f"###### _Proyecto: {task.get('project', 'No asignado')}_")
            st.caption(f"Añadida por: {task.get('added_by', 'Admin')} (Semana {task['week_added']})")
            st.write(task['desc'])

            action_cols = st.columns(2) # ... (resto de la lógica de tomar/eliminar tarea sin cambios)...
            if user_role == "collaborator":
                with action_cols[0]:
                    if st.button("🙋‍♂️ Tomar esta Tarea", key=f"take_task_{task['id']}"):
                        entry_key = f"{user}_{current_week}"
                        if entry_key not in st.session_state.weekly_entries:
                            st.session_state.weekly_entries[entry_key] = {'hours': 0, 'tasks': []}
                        if 'tasks' not in st.session_state.weekly_entries[entry_key] or \
                           not isinstance(st.session_state.weekly_entries[entry_key]['tasks'], list):
                            st.session_state.weekly_entries[entry_key]['tasks'] = []
                        user_task_ids = [t['id'] for t in st.session_state.weekly_entries[entry_key]['tasks']]
                        if task['id'] not in user_task_ids:
                            taken_task_copy = task.copy()
                            taken_task_copy['status'] = TASK_STATUSES[0]
                            st.session_state.weekly_entries[entry_key]['tasks'].append(taken_task_copy)
                            save_data(WEEKLY_ENTRIES_FILE, st.session_state.weekly_entries)
                        tasks_to_remove_indices.append(i)
                        st.success(f"Has tomado la tarea: '{task['title']}'")
            if user_role == "admin":
                with action_cols[user_role != "collaborator"]:
                    if st.button("🗑️ Eliminar Tarea Libre", key=f"admin_delete_unassigned_{task['id']}", type="secondary"):
                        tasks_to_remove_indices.append(i)
                        st.warning(f"Tarea libre '{task['title']}' marcada para eliminación.")
        st.markdown("---")
    
    if tasks_to_remove_indices:
        for index in sorted(list(set(tasks_to_remove_indices)), reverse=True):
            del st.session_state.unassigned_tasks[index]
        save_data(UNASSIGNED_TASKS_FILE, st.session_state.unassigned_tasks); st.rerun()


# --- MODIFICADO: historical_data_page ---
def historical_data_page():
    st.header("📊 Datos Históricos")
    st.subheader("Planificaciones Semanales de Colaboradores")
    if st.session_state.weekly_entries:
        history_data = []
        all_projects_in_history = set() # Para el filtro de proyectos

        for entry_key, data_entry in st.session_state.weekly_entries.items():
            user_id_hist, week_hist = entry_key.split("_", 1)
            user_full_name_hist = st.session_state.users_db.get(user_id_hist, {}).get("full_name", user_id_hist)
            
            num_tasks_hist = len(data_entry.get('tasks', []))
            task_details_hist = []
            for t_hist in data_entry.get('tasks', []):
                project_name_hist = t_hist.get('project', 'N/A')
                all_projects_in_history.add(project_name_hist) # Añadir al set para el filtro
                task_details_hist.append(f"{t_hist['title']} ({project_name_hist} - {t_hist.get('status', 'N/A')})")

            history_data.append({
                "Semana": week_hist, "Colaborador": user_full_name_hist,
                "Horas Planificadas": data_entry.get('hours', 0), "Nº Tareas": num_tasks_hist,
                "Tareas (Proyecto - Estado)": "; ".join(task_details_hist) if task_details_hist else "N/A"
            })
        
        if history_data:
            df_history = pd.DataFrame(history_data)
            
            filter_cols = st.columns(3) # Añadida una columna para el filtro de proyecto
            with filter_cols[0]:
                weeks_available_hist = ["Todas"] + sorted(list(df_history["Semana"].unique()))
                selected_week_hist = st.selectbox("Filtrar por Semana:", options=weeks_available_hist, key="hist_week_filter_main")
            with filter_cols[1]:
                users_available_hist = ["Todos"] + sorted(list(df_history["Colaborador"].unique()))
                selected_user_hist = st.selectbox("Filtrar por Colaborador:", options=users_available_hist, key="hist_user_filter_main")
            # NUEVO: Filtro por Proyecto
            with filter_cols[2]:
                projects_for_filter = ["Todos"] + sorted(list(all_projects_in_history))
                selected_project_hist = st.selectbox("Filtrar por Proyecto:", options=projects_for_filter, key="hist_project_filter_main")


            filtered_df_hist = df_history.copy()
            if selected_week_hist != "Todas":
                filtered_df_hist = filtered_df_hist[filtered_df_hist["Semana"] == selected_week_hist]
            if selected_user_hist != "Todos":
                filtered_df_hist = filtered_df_hist[filtered_df_hist["Colaborador"] == selected_user_hist]
            # NUEVO: Aplicar filtro de proyecto
            if selected_project_hist != "Todos":
                # Este filtro es más complejo porque el proyecto está dentro de un string.
                # Filtraremos si la cadena del proyecto seleccionado aparece en la columna "Tareas (Proyecto - Estado)"
                filtered_df_hist = filtered_df_hist[filtered_df_hist["Tareas (Proyecto - Estado)"].str.contains(selected_project_hist, case=False, na=False)]

            st.dataframe(filtered_df_hist, use_container_width=True)
        else: st.info("No hay datos de planificaciones semanales con el formato esperado.")
    else: st.info("No hay datos de planificaciones semanales registrados.")

    st.subheader("Resumen de Votos Semanales (Promedio por Colaborador Votado)")
    # ... (Código de votos en historial se mantiene igual, no afectado directamente por proyectos) ...
    if st.session_state.votes:
        vote_data_hist = []
        for vote_key_hist, score_hist in st.session_state.votes.items():
            try:
                voter_id_hist, week_vote_hist, target_user_id_hist = vote_key_hist.split("_", 2)
                target_full_name_hist = st.session_state.users_db.get(target_user_id_hist, {}).get("full_name", target_user_id_hist)
                vote_data_hist.append({
                    "Semana": week_vote_hist, "Colaborador Votado": target_full_name_hist,
                    "Puntuación": score_hist
                })
            except ValueError: continue
        
        if vote_data_hist:
            df_votes_hist = pd.DataFrame(vote_data_hist)
            if not df_votes_hist.empty:
                df_avg_votes_hist = df_votes_hist.groupby(['Semana', 'Colaborador Votado'])['Puntuación'].agg(['mean', 'count']).reset_index()
                df_avg_votes_hist.rename(columns={'mean': 'Promedio Puntuación', 'count': 'Número de Votos'}, inplace=True)
                df_avg_votes_hist['Promedio Puntuación'] = df_avg_votes_hist['Promedio Puntuación'].round(2)
                filter_vote_cols = st.columns(2)
                with filter_vote_cols[0]:
                    weeks_vote_available = ["Todas"] + sorted(list(df_avg_votes_hist["Semana"].unique()))
                    selected_week_vote_hist = st.selectbox("Filtrar Semana (Votos):", options=weeks_vote_available, key="vote_week_filter_main")
                with filter_vote_cols[1]:
                    users_vote_available = ["Todos"] + sorted(list(df_avg_votes_hist["Colaborador Votado"].unique()))
                    selected_user_vote_hist = st.selectbox("Filtrar Colaborador Votado:", options=users_vote_available, key="vote_user_filter_main")
                filtered_df_avg_votes_hist = df_avg_votes_hist.copy()
                if selected_week_vote_hist != "Todas":
                    filtered_df_avg_votes_hist = filtered_df_avg_votes_hist[filtered_df_avg_votes_hist["Semana"] == selected_week_vote_hist]
                if selected_user_vote_hist != "Todos":
                    filtered_df_avg_votes_hist = filtered_df_avg_votes_hist[filtered_df_avg_votes_hist["Colaborador Votado"] == selected_user_vote_hist]
                st.dataframe(filtered_df_avg_votes_hist, use_container_width=True)
                if st.session_state.user_role == 'admin' and st.checkbox("Mostrar detalle de votos individuales (Solo Admin)", key="admin_show_raw_votes_main"):
                    st.dataframe(df_votes_hist, use_container_width=True)
            else: st.info("No hay datos de votos para mostrar en el resumen.")
        else: st.info("No hay datos de votos registrados con formato correcto.")
    else: st.info("No hay datos de votos registrados.")


# --- Aplicación Principal (Main) ---
def main():
    st.set_page_config(page_title="Gestor Semanal del Equipo", layout="wide", initial_sidebar_state="expanded")
    initialize_data()

    if st.session_state.get('force_password_reset_for_user'):
        new_password_setup_page(st.session_state.force_password_reset_for_user)
    elif not st.session_state.get('logged_in_user'):
        login_page()
    else:
        st.sidebar.title(f"👋 Hola, {st.session_state.user_full_name}")
        st.sidebar.caption(f"Rol: {st.session_state.user_role.title()}")
        st.sidebar.markdown("---")
        menu_options = {
            "📝 Mi Plan Semanal": "weekly_input_page", "🤝 Hub del Equipo": "team_hub_page",
            "🎯 Tareas Libres": "unassigned_tasks_page", "📊 Datos Históricos": "historical_data_page"
        }
        if 'main_menu_selection' not in st.session_state:
            st.session_state.main_menu_selection = list(menu_options.keys())[0]
        selected_page_title = st.sidebar.radio(
            "Menú Principal", list(menu_options.keys()), key="main_menu_selection_widget",
            on_change=lambda: st.session_state.update(main_menu_selection=st.session_state.main_menu_selection_widget)
        )
        st.sidebar.markdown("---")
        if st.sidebar.button("🚪 Cerrar Sesión", key="logout_main_button_page", use_container_width=True):
            logout(); return
        
        if st.session_state.main_menu_selection == "📝 Mi Plan Semanal": weekly_input_page()
        elif st.session_state.main_menu_selection == "🤝 Hub del Equipo": team_hub_page()
        elif st.session_state.main_menu_selection == "🎯 Tareas Libres": unassigned_tasks_page()
        elif st.session_state.main_menu_selection == "📊 Datos Históricos": historical_data_page()

if __name__ == "__main__":
    main()