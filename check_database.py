from app import app, db, User, ExamRecord, Note, Favorite

def check_database():
    with app.app_context():
        print("\n=== 用戶資料 ===")
        users = User.query.all()
        for user in users:
            print(f"用戶 ID: {user.id}, 用戶名: {user.username}")

        print("\n=== 考試記錄 ===")
        records = ExamRecord.query.all()
        for record in records:
            print(f"記錄 ID: {record.id}, 用戶 ID: {record.user_id}, 考試: {record.exam_id}, 分數: {record.score}")

        print("\n=== 筆記 ===")
        notes = Note.query.all()
        for note in notes:
            print(f"筆記 ID: {note.id}, 用戶 ID: {note.user_id}, 考試記錄 ID: {note.exam_record_id}, 題號: {note.question_number}")
            print(f"內容: {note.content[:50]}...")  # 只顯示前50個字符

        print("\n=== 收藏 ===")
        favorites = Favorite.query.all()
        for favorite in favorites:
            print(f"收藏 ID: {favorite.id}, 用戶 ID: {favorite.user_id}, 考試: {favorite.exam_id}, 題號: {favorite.question_number}")

if __name__ == '__main__':
    check_database()
