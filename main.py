from sanic import Sanic
from sanic.response import html, json, redirect
from jinja2 import Environment, FileSystemLoader
import aiomysql

app = Sanic("MyAPI")

# Setup Jinja2 template environment
env = Environment(loader=FileSystemLoader('templates'))

# Membuat Koneksi database
@app.listener('before_server_start')
async def setup_db(app, loop):
    app.ctx.pool = await aiomysql.create_pool(
        host='localhost',
        port=3306,
        user='root',
        password='',
        db='express',
        loop=loop
    )

# Menutup koneksi database
@app.listener('after_server_stop')
async def close_db(app, loop):
    app.ctx.pool.close()
    await app.ctx.pool.wait_closed()

# Halaman users
@app.route("/users", methods=["GET"])
async def get_users(request):
    async with app.ctx.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("SELECT * FROM user")
            result = await cursor.fetchall()
            users = [{"id": row[0], "name": row[1], "email": row[2]} for row in result]
            
            # Render template with data
            template = env.get_template('users.html')
            rendered_template = template.render(users=users)
            return html(rendered_template)

# Halaman detail user
@app.route("/user/<user_id>", methods=["GET"])
async def get_user_by_id(request, user_id):
    async with app.ctx.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("SELECT * FROM user WHERE id = %s", (user_id,))
            result = await cursor.fetchone()
            if result:
                user = {"id": result[0], "name": result[1], "email": result[2]}
            else:
                user = None

            # Render template with data
            template = env.get_template('user_detail.html')
            rendered_template = template.render(user=user)
            return html(rendered_template)
        

# Halaman tamabah user
@app.route("/add_user", methods=["GET"])
async def add_user_form(request):
    template = env.get_template('add_user.html')
    rendered_template = template.render()
    return html(rendered_template)

# Fungsi tambah data
@app.route("/user", methods=["POST"])
async def add_user(request):
    name = request.form.get('name')
    email = request.form.get('email')
    if not name or not email:
        return json({"error": "Name and age are required fields."}, status=400)

    async with app.ctx.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("INSERT INTO user (name, email) VALUES (%s, %s)", (name, email))
            await conn.commit()
            return redirect("/users")


# Halaman Edit data
@app.route("/user/<user_id>/edit", methods=["GET"])
async def edit_user_form(request, user_id):
    async with app.ctx.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("SELECT * FROM user WHERE id = %s", (user_id,))
            result = await cursor.fetchone()
            if result:
                user = {"id": result[0], "name": result[1], "email": result[2]}
            else:
                user = None

            # Render template with data
            template = env.get_template('update_user.html')
            rendered_template = template.render(user=user)
            return html(rendered_template)
# Fungsi tambah data
@app.route("/user/<user_id>", methods=["POST"])
async def update_user(request, user_id):
    name = request.form.get('name')
    email = request.form.get('email')
    if not name or not email:
        return json({"error": "Name and age are required fields."}, status=400)

    async with app.ctx.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("UPDATE user SET name = %s, email = %s WHERE id = %s", (name, email, user_id))
            await conn.commit()
            return redirect("/users")


# Fungsi delete data
@app.route("/user/<user_id>", methods=["POST"])
async def delete_user(request, user_id):
    if request.form.get('_method') == 'DELETE':
        async with app.ctx.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("DELETE FROM user WHERE id = %s", (user_id,))
                await conn.commit()
                return redirect("/users")
    return json({"error": "Invalid request method"}, status=400)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
