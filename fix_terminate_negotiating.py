"""
临时脚本：处理terminate_negotiating状态的合同
此脚本用于修复无法操作的合同记录
"""
from app.db.session import SessionLocal
from app.models.contract import Contract
from app.models.contract_termination_request import ContractTerminationRequest
from app.core.enums import ContractStatus

def fix_terminate_negotiating_contracts():
    """修复terminate_negotiating状态的合同"""
    db = SessionLocal()
    try:
        # 查找所有terminate_negotiating状态的合同
        contracts = db.query(Contract).filter(
            Contract.status == 'terminate_negotiating'
        ).all()
        
        print(f"找到 {len(contracts)} 条terminate_negotiating状态的合同:")
        
        for contract in contracts:
            print(f"\n处理合同 ID: {contract.id}, 合同号: {contract.contract_no}")
            print(f"  房东ID: {contract.landlord_id}, 租客ID: {contract.tenant_id}")
            
            # 检查是否有待处理的解约申请
            pending_request = db.query(ContractTerminationRequest).filter(
                ContractTerminationRequest.contract_id == contract.id,
                ContractTerminationRequest.status == 'pending'
            ).first()
            
            if pending_request:
                print(f"  找到待处理的解约申请 ID: {pending_request.id}")
                print(f"  发起人: {pending_request.initiator_id}")
                print(f"  解约原因: {pending_request.termination_reason[:50]}...")
                
                # 方案1：将合同状态恢复为ACTIVE，并将解约申请标记为拒绝
                print(f"\n  执行操作：恢复合同状态为ACTIVE，拒绝解约申请")
                
                # 恢复合同状态
                contract.status = ContractStatus.ACTIVE
                
                # 拒绝解约申请
                pending_request.status = 'rejected'
                pending_request.response_opinion = '系统自动处理：因无法操作，自动拒绝此申请'
                pending_request.responder_id = pending_request.initiator_id  # 临时设置
                from datetime import datetime
                pending_request.responded_at = datetime.utcnow()
                
                print(f"  ✓ 合同状态已恢复为: {contract.status}")
                print(f"  ✓ 解约申请状态已设置为: {pending_request.status}")
            else:
                print(f"  未找到待处理的解约申请")
                print(f"  执行操作：直接将合同状态恢复为ACTIVE")
                
                # 直接恢复合同状态
                contract.status = ContractStatus.ACTIVE
                print(f"  ✓ 合同状态已恢复为: {contract.status}")
        
        # 提交所有更改
        db.commit()
        print(f"\n✓ 成功处理 {len(contracts)} 条合同记录")
        
    except Exception as e:
        print(f"\n✗ 处理失败: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("开始处理terminate_negotiating状态的合同")
    print("=" * 60)
    
    fix_terminate_negotiating_contracts()
    
    print("\n" + "=" * 60)
    print("处理完成！")
    print("=" * 60)
