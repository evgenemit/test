import aiosqlite
from datetime import datetime, timedelta

from services.password import create_random_string, hash_password, verify_password
from schemas import auth, orders


ORDER_STATUS = {
    -2: 'Отменен продавцом',
    -1: 'Отменен покупателем',
    0: 'Создан',
    1: 'Принят',
    2: 'В пути',
    3: 'Готов к получению',
    4: 'Завершен'
}


class Database:
    async def connect(self) -> None:
        self.db = await aiosqlite.connect('./db.sqlite3')

    async def disconnect(self) -> None:
        await self.db.close()

    async def execute(self, query: str) -> None:
        await self.db.execute(query)
        await self.db.commit()

    async def fetchone(self, query: str):
        async with self.db.execute(query) as cursor:
            data = await cursor.fetchone()
            return data

    async def fetchall(self, query: str) -> list:
        async with self.db.execute(query) as cursor:
            data = await cursor.fetchall()
            return data

    async def __create_user(self, password: str, email: str, role: str) -> int|None:
        """Создает пользователя"""
        salt = create_random_string()
        hashed_password = hash_password(password, salt).hex()
        try:
            await self.execute(
                f"""
                INSERT INTO users (password, salt, email, role) VALUES
                ('{hashed_password}', '{salt}', '{email}', '{role}');
                """
            )
        except aiosqlite.IntegrityError:
            return None
        user_id = (await self.fetchone(f"SELECT id FROM users WHERE email = '{email}';"))[0]
        return user_id

    async def create_admin(self) -> None:
        """Создает админа"""
        await self.__create_user('admin', 'admin', 'ad')

    async def create_client(self, user: auth.CreateClient) -> dict:
        """Создает покупателя"""
        user_id = await self.__create_user(user.password, user.email, 'cl')
        if user_id is None:
            return {'status': False, 'detail': 'email уже используется'}
        await self.execute(
            f"""
            INSERT INTO clients (user_id, first_name) VALUES ({user_id}, '{user.first_name}');
            """
        )
        return {'status': True}

    async def create_seller(self, user: auth.CreateSeller) -> dict:
        """Создает продавца"""
        user_id = await self.__create_user(user.password, user.email, 'sl')
        if user_id is None:
            return {'status': False, 'detail': 'email уже используется'}
        await self.execute(
            f"""
            INSERT INTO sellers (user_id, name, about) VALUES ({user_id}, '{user.name}', '{user.about}');
            """
        )
        return {'status': True}

    async def create_point(self, user: auth.CreatePoint) -> dict:
        """Создает пункт выдачи"""
        user_id = await self.__create_user(user.password, user.email, 'pt')
        if user_id is None:
            return {'status': False, 'detail': 'email уже используется'}
        await self.execute(
            f"""
            INSERT INTO points (user_id, name) VALUES ({user_id}, '{user.name}');
            """
        )
        return {'status': True}

    async def authenticate(self, email: str, password: str) -> dict:
        """Аутентификация"""
        user = await self.fetchone(f"SELECT id, password, salt, role FROM users WHERE email = '{email}';")
        if user is None:
            return {'status': False, 'detail': 'неправильный email или пароль'}
        user_id, old_hash, salt, role = user
        if role == 'sl':
            active = (await self.fetchone(f"SELECT active FROM sellers WHERE user_id = {user_id};"))[0]
            if not active:
                return {'status': False, 'detail': 'аккаунт не активирован'}
        elif role == 'pt':
            active = (await self.fetchone(f"SELECT active FROM points WHERE user_id = {user_id};"))[0]
            if not active:
                return {'status': False, 'detail': 'аккаунт не активирован'}
        if verify_password(password, old_hash, salt):
            return {'status': True, 'user_id': user_id}
        return {'status': False, 'detail': 'неправильный email или пароль'}

    async def create_session(self, form: auth.Login) -> dict:
        """Создает сессии"""
        res = await self.authenticate(form.email, form.password)
        if not res['status']:
            return res
        token = create_random_string(20)
        # TODO: проверять существует ли токен
        await db.execute(f"INSERT INTO sessions (user_id, token) VALUES ({res['user_id']}, '{token}') ON CONFLICT(user_id) DO UPDATE SET token = '{token}';")
        return {'status': True, 'token': token}

    async def check_session(self, token: str) -> bool:
        """Проверяет активна ли сессия"""
        session = await self.fetchone(f"SELECT user_id, created_at FROM sessions WHERE token = '{token}';")
        if session is None:
            return False
        user_id, created_at = session
        created_at = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
        # TODO: продливать сессию
        if (datetime.now() - created_at) > timedelta(hours=1):
            await self.execute(f"DELETE FROM sessions WHERE user_id = {user_id};")
            return False
        return True

    async def delete_session(self, token: str):
        """Удаляет сессию"""
        await self.execute(f"DELETE FROM sessions WHERE token = '{token}';")

    async def get_user_info_by_token(self, token: str) -> str:
        """Возвращет роль, id пользователя по токену сессии"""
        user = await self.fetchone(
            f"""
            SELECT role, id FROM users WHERE id =
            (SELECT user_id FROM sessions WHERE token = '{token}');
            """
        )
        return user[0], user[1]

    async def get_seller_info_by_id(self, uid: int):
        seller = await self.fetchone(f"SELECT name FROM sellers WHERE id = {uid};")
        if seller is None:
            return {'status': False, 'detail': 'продавец не существует'}
        return {'status': True, 'name': seller[0]}

    async def get_points(self):
        data = await self.fetchall(f"SELECT id, name FROM points WHERE active = 1;")
        points = []
        for point_data in data:
            points.append({
                'id': point_data[0],
                'name': point_data[1]
            })
        return {'status': True, 'points': points}

    async def create_order(self, order: orders.Order):
        """Создает заказ"""
        await self.execute(
            f"""
            INSERT INTO orders (client_id, seller_id, point_id, about)
            VALUES ((SELECT id FROM clients WHERE user_id = {order.client_id}), {order.seller_id}, {order.point_id}, '{order.about}');
            """
        )

    async def get_orders(self, role: str, uid: int):
        """Возвращает заказы пользователя"""
        orders = []
        completed_orders = []
        if role == 'cl':
            all_orders = await self.fetchall(
                f"""
                SELECT orders.id, status, points.name FROM orders
                JOIN points ON point_id = points.id
                WHERE client_id = (SELECT id FROM clients WHERE user_id = {uid})
                ORDER BY status DESC;
                """
            )
            for order in all_orders:
                order_data = {
                    'id': order[0],
                    'status': ORDER_STATUS.get(order[1], 'Статус'),
                    'address': order[2]
                }
                if order[1] in [0, 1, 2, 3]:
                    orders.append(order_data)
                else:
                    completed_orders.append(order_data)
        elif role == 'sl':
            all_orders = await self.fetchall(
                f"""
                SELECT orders.id, status, clients.first_name FROM orders
                JOIN clients ON client_id = clients.id
                WHERE seller_id = (SELECT id FROM sellers WHERE user_id = {uid})
                ORDER BY status DESC;
                """
            )
            for order in all_orders:
                order_data = {
                    'id': order[0],
                    'status': ORDER_STATUS.get(order[1], 'Статус'),
                    'first_name': order[2]
                }
                if order[1] in [0, 1]:
                    orders.append(order_data)
                else:
                    completed_orders.append(order_data)
        return {'status': True, 'orders': orders, 'completed_orders': completed_orders}

    async def get_order(self, order_id: int, role: str):
        order = await self.fetchone(
            f"""
            SELECT sellers.name, points.name, orders.about, orders.status, clients.first_name FROM orders
            JOIN clients ON clients.id = client_id
            JOIN sellers ON sellers.id = seller_id
            JOIN points ON points.id = point_id WHERE orders.id = {order_id};
            """
        )
        return {
            'status': True,
            'first_name': order[4],
            'seller_name': order[0],
            'point_name': order[1],
            'about': order[2],
            'can_cancle': order[3] in [0, 1],
            'can_accept': order[3] == 0
        }

    async def cancle_order(self, order_id: int, role: str):
        if role == 'cl':
            await self.execute(
                f"""
                UPDATE orders SET status = -1 WHERE id = {order_id};
                """
            )
        elif role == 'sl':
            await self.execute(
                f"""
                UPDATE orders SET status = -2 WHERE id = {order_id};
                """
            )
        return {'status': True}

    async def update_order_status(self, order_id: int, status: int):
        await self.execute(
            f"UPDATE orders SET status = {status} WHERE id = {order_id};"
        )
        return {'status': True}


db = Database()
