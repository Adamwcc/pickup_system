# 位於 app/routers/teachers.py

# ... (其他 import 和 API 保持不變) ...

# 找到 create_student_by_teacher 並替換它
@router.post("/students/", response_model=schemas.StudentOut, summary="老師新增學生並邀請家長")
def create_student_by_teacher(
    student_data: schemas.StudentCreateByTeacher,
    db: Session = Depends(get_db),
    current_teacher: models.User = Depends(get_current_teacher_user)
):
    """
    由已登入的老師或管理員，在其所屬的機構下建立一位新學生，
    並為其關聯的家長建立「預註冊(invited)」帳號。
    """
    if not current_teacher.institution_id:
        raise HTTPException(status_code=400, detail="操作失敗：您的帳號未歸屬任何機構")
    
    if not student_data.parents:
        raise HTTPException(status_code=400, detail="操作失敗：必須提供至少一位家長的資訊")

    # 1. 建立學生
    student = crud.create_student_for_institution(
        db=db, 
        full_name=student_data.student_full_name, 
        institution_id=current_teacher.institution_id
    )

    # 2. 為每一位提供的家長建立預註冊帳號並綁定
    for parent_info in student_data.parents:
        crud.pre_register_parent_and_link_student(
            db=db,
            student_id=student.id,
            parent_phone=parent_info.phone_number,
            parent_full_name=parent_info.full_name
        )
    
    # 重新查詢學生資訊以包含最新的關聯
    db.refresh(student)
    return student
