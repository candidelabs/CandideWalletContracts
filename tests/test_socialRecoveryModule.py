#!/usr/bin/python3

from brownie import reverts, chain
from eth_account import Account
from testUtils import ExecuteExecTransaction, ExecuteSocialRecoveryOperation


def test_guardian_storage(
    candideWalletProxy, owner, accounts, socialRecoveryModule
):
    firstGuardian = Account.create()
    secondGuardian = Account.create()
    thirdGuardian = Account.create()

    # with reverts("SM: unauthorized"):
    try:
        socialRecoveryModule.addGuardianWithThreshold(
            candideWalletProxy.address,
            firstGuardian.address,
            1,
            {"from": accounts[0]},
        )
    except Exception as badResponseFormat:
        #this is raising web3.exceptions.BadResponseFormat now !!!
        assert "SM: unauthorized" in badResponseFormat.args[0]

    # with reverts("GS: methold only callable by an enabled module"):
    try:
        socialRecoveryModule.addGuardianWithThreshold(
            candideWalletProxy.address,
            firstGuardian.address,
            1,
            {"from": candideWalletProxy},
        )
    except Exception as badResponseFormat:
        #this is raising web3.exceptions.BadResponseFormat now !!!
        assert "GS: methold only callable by an enabled module" in badResponseFormat.args[0]

    # Enable social recovery module for Safe
    callData = candideWalletProxy.enableModule.encode_input(
        socialRecoveryModule.address
    )
    ExecuteExecTransaction(
        candideWalletProxy.address,
        0,
        callData,
        0,
        0,
        0,
        0,
        "0x0000000000000000000000000000000000000000",
        "0x0000000000000000000000000000000000000000",
        owner,
        owner,
        candideWalletProxy,
    )

    assert candideWalletProxy.isModuleEnabled(socialRecoveryModule.address)

    # guardian cannot be the wallet itself
    callData = socialRecoveryModule.addGuardianWithThreshold.encode_input(
        candideWalletProxy.address, candideWalletProxy.address, 1
    )
    # try:
    try:
        ExecuteSocialRecoveryOperation(
            callData,
            candideWalletProxy,
            socialRecoveryModule,
            owner,
        )
        assert False #hacky way to assert revert
    except Exception as badResponseFormat:
        #this is raising web3.exceptions.BadResponseFormat now !!!
        pass

    # guardian cannot be an owner of the wallet
    callData = socialRecoveryModule.addGuardianWithThreshold.encode_input(
        candideWalletProxy.address, owner.address, 1
    )
    try:
        ExecuteSocialRecoveryOperation(
            callData,
            candideWalletProxy,
            socialRecoveryModule,
            owner,
        )
        assert False #hacky way to assert revert
    except Exception as badResponseFormat:
        #this is raising web3.exceptions.BadResponseFormat now !!!
        pass

    # threshold cannot be higher than number of guardians after addition
    callData = socialRecoveryModule.addGuardianWithThreshold.encode_input(
        candideWalletProxy.address, firstGuardian.address, 2
    )
    try:
        ExecuteSocialRecoveryOperation(
            callData,
            candideWalletProxy,
            socialRecoveryModule,
            owner,
        )
        assert False #hacky way to assert revert
    except Exception as badResponseFormat:
        #this is raising web3.exceptions.BadResponseFormat now !!!
        pass

    # threshold cannot be 0
    callData = socialRecoveryModule.addGuardianWithThreshold.encode_input(
        candideWalletProxy.address, firstGuardian.address, 0
    )
    try:
        ExecuteSocialRecoveryOperation(
            callData,
            candideWalletProxy,
            socialRecoveryModule,
            owner,
        )
        assert False #hacky way to assert revert
    except Exception as badResponseFormat:
        #this is raising web3.exceptions.BadResponseFormat now !!!
        pass

    # Add first guardian
    callData = socialRecoveryModule.addGuardianWithThreshold.encode_input(
        candideWalletProxy.address, firstGuardian.address, 1
    )
    ExecuteSocialRecoveryOperation(
        callData,
        candideWalletProxy,
        socialRecoveryModule,
        owner,
    )
    assert socialRecoveryModule.isGuardian(
        candideWalletProxy.address, firstGuardian.address
    )

    # Add second guardian
    callData = socialRecoveryModule.addGuardianWithThreshold.encode_input(
        candideWalletProxy.address, secondGuardian.address, 1
    )
    ExecuteSocialRecoveryOperation(
        callData,
        candideWalletProxy,
        socialRecoveryModule,
        owner,
    )

    # Add third guardian with threshold 2
    callData = socialRecoveryModule.addGuardianWithThreshold.encode_input(
        candideWalletProxy.address, thirdGuardian.address, 2
    )
    ExecuteSocialRecoveryOperation(
        callData,
        candideWalletProxy,
        socialRecoveryModule,
        owner,
    )

    assert socialRecoveryModule.getGuardians(candideWalletProxy.address) == [
        thirdGuardian.address,
        secondGuardian.address,
        firstGuardian.address,
    ]

    # cannot add an existing guardian
    callData = socialRecoveryModule.addGuardianWithThreshold.encode_input(
        candideWalletProxy.address, secondGuardian.address, 2
    )
    try:
        ExecuteSocialRecoveryOperation(
            callData,
            candideWalletProxy,
            socialRecoveryModule,
            owner,
        )
        assert False #hacky way to assert revert
    except Exception as badResponseFormat:
        #this is raising web3.exceptions.BadResponseFormat now !!!
        pass

    # cannot add a guardian with address(0x0)
    callData = socialRecoveryModule.addGuardianWithThreshold.encode_input(
        candideWalletProxy.address,
        "0x0000000000000000000000000000000000000000",
        2,
    )
    try:
        ExecuteSocialRecoveryOperation(
            callData,
            candideWalletProxy,
            socialRecoveryModule,
            owner,
        )
        assert False #hacky way to assert revert
    except Exception as badResponseFormat:
        #this is raising web3.exceptions.BadResponseFormat now !!!
        pass

    # cannot add a guardian with address(0x1)
    callData = socialRecoveryModule.addGuardianWithThreshold.encode_input(
        candideWalletProxy.address,
        "0x0000000000000000000000000000000000000001",
        2,
    )
    try:
        ExecuteSocialRecoveryOperation(
            callData,
            candideWalletProxy,
            socialRecoveryModule,
            owner,
        )
        assert False #hacky way to assert revert
    except Exception as badResponseFormat:
        #this is raising web3.exceptions.BadResponseFormat now !!!
        pass

    # cannot change threshold to 0 if guardians > 0
    callData = socialRecoveryModule.changeThreshold.encode_input(
        candideWalletProxy.address, 0
    )
    try:
        ExecuteSocialRecoveryOperation(
            callData,
            candideWalletProxy,
            socialRecoveryModule,
            owner,
        )
        assert False #hacky way to assert revert
    except Exception as badResponseFormat:
        #this is raising web3.exceptions.BadResponseFormat now !!!
        pass

    # cannot change threshold higher than guardians count
    callData = socialRecoveryModule.changeThreshold.encode_input(
        candideWalletProxy.address, 6
    )
    try:
        ExecuteSocialRecoveryOperation(
            callData,
            candideWalletProxy,
            socialRecoveryModule,
            owner,
        )
        assert False #hacky way to assert revert
    except Exception as badResponseFormat:
        #this is raising web3.exceptions.BadResponseFormat now !!!
        pass

    # change threshold from 2 to 1
    callData = socialRecoveryModule.changeThreshold.encode_input(
        candideWalletProxy.address, 1
    )
    ExecuteSocialRecoveryOperation(
        callData,
        candideWalletProxy,
        socialRecoveryModule,
        owner,
    )

    assert socialRecoveryModule.threshold(candideWalletProxy.address) == 1

    # cannot revoke a non-guardian
    callData = socialRecoveryModule.revokeGuardianWithThreshold.encode_input(
        candideWalletProxy.address,
        "0x0000000000000000000000000000000000000001",
        accounts[5].address,
        1,
    )
    try:
        ExecuteSocialRecoveryOperation(
            callData,
            candideWalletProxy,
            socialRecoveryModule,
            owner,
        )
        assert False #hacky way to assert revert
    except Exception as badResponseFormat:
        #this is raising web3.exceptions.BadResponseFormat now !!!
        pass

    # cannot have threshold higher than number of guardians after revoking
    callData = socialRecoveryModule.revokeGuardianWithThreshold.encode_input(
        candideWalletProxy.address,
        "0x0000000000000000000000000000000000000001",
        thirdGuardian.address,
        6,
    )
    try:
        ExecuteSocialRecoveryOperation(
            callData,
            candideWalletProxy,
            socialRecoveryModule,
            owner,
        )
        assert False #hacky way to assert revert
    except Exception as badResponseFormat:
        #this is raising web3.exceptions.BadResponseFormat now !!!
        pass

    # cannot have threshold 0 if guardians > 0 after removal
    callData = socialRecoveryModule.revokeGuardianWithThreshold.encode_input(
        candideWalletProxy.address,
        "0x0000000000000000000000000000000000000001",
        thirdGuardian.address,
        0,
    )
    try:
        ExecuteSocialRecoveryOperation(
            callData,
            candideWalletProxy,
            socialRecoveryModule,
            owner,
        )
        assert False #hacky way to assert revert
    except Exception as badResponseFormat:
        #this is raising web3.exceptions.BadResponseFormat now !!!
        pass

    # revert if invalid previous guardian
    callData = socialRecoveryModule.revokeGuardianWithThreshold.encode_input(
        candideWalletProxy.address,
        firstGuardian.address,
        thirdGuardian.address,
        1,
    )
    try:
        ExecuteSocialRecoveryOperation(
            callData,
            candideWalletProxy,
            socialRecoveryModule,
            owner,
        )
        assert False #hacky way to assert revert
    except Exception as badResponseFormat:
        #this is raising web3.exceptions.BadResponseFormat now !!!
        pass

    # remove third guardian
    callData = socialRecoveryModule.revokeGuardianWithThreshold.encode_input(
        candideWalletProxy.address,
        "0x0000000000000000000000000000000000000001",
        thirdGuardian.address,
        1,
    )
    ExecuteSocialRecoveryOperation(
        callData,
        candideWalletProxy,
        socialRecoveryModule,
        owner,
    )

    # remove second guardian
    callData = socialRecoveryModule.revokeGuardianWithThreshold.encode_input(
        candideWalletProxy.address,
        "0x0000000000000000000000000000000000000001",
        secondGuardian.address,
        1,
    )
    ExecuteSocialRecoveryOperation(
        callData,
        candideWalletProxy,
        socialRecoveryModule,
        owner,
    )

    # remove first guardian
    callData = socialRecoveryModule.revokeGuardianWithThreshold.encode_input(
        candideWalletProxy.address,
        "0x0000000000000000000000000000000000000001",
        firstGuardian.address,
        0,
    )
    ExecuteSocialRecoveryOperation(
        callData,
        candideWalletProxy,
        socialRecoveryModule,
        owner,
    )

    assert socialRecoveryModule.getGuardians(candideWalletProxy.address) == []
    assert not socialRecoveryModule.isGuardian(
        candideWalletProxy.address, firstGuardian.address
    )
    assert not socialRecoveryModule.isGuardian(
        candideWalletProxy.address, secondGuardian.address
    )
    assert not socialRecoveryModule.isGuardian(
        candideWalletProxy.address, thirdGuardian.address
    )


# Test using multiConfirmRecovery
def test_multiConfirmRecovery(
    candideWalletProxy, owner, accounts, socialRecoveryModule
):
    firstGuardian = Account.create()
    secondGuardian = Account.create()
    thirdGuardian = Account.create()

    # Enable social recovery module for Safe
    callData = candideWalletProxy.enableModule.encode_input(
        socialRecoveryModule.address
    )
    ExecuteExecTransaction(
        candideWalletProxy.address,
        0,
        callData,
        0,
        0,
        0,
        0,
        "0x0000000000000000000000000000000000000000",
        "0x0000000000000000000000000000000000000000",
        owner,
        owner,
        candideWalletProxy,
    )

    assert candideWalletProxy.isModuleEnabled(socialRecoveryModule.address)

    newOwner1 = Account.create()
    newOwner2 = Account.create()
    newOwner3 = Account.create()

    # Revert if no guardians exist for the wallet
    try:
        socialRecoveryModule.executeRecovery(
            candideWalletProxy.address,
            [newOwner1.address],
            1,
        )
        assert False #hacky way to assert revert
    except Exception as badResponseFormat:
        #this is raising web3.exceptions.BadResponseFormat now !!!
        pass

    # Add first guardian
    callData = socialRecoveryModule.addGuardianWithThreshold.encode_input(
        candideWalletProxy.address, firstGuardian.address, 1
    )
    ExecuteSocialRecoveryOperation(
        callData,
        candideWalletProxy,
        socialRecoveryModule,
        owner,
    )

    # Add second guardian
    callData = socialRecoveryModule.addGuardianWithThreshold.encode_input(
        candideWalletProxy.address, secondGuardian.address, 1
    )
    ExecuteSocialRecoveryOperation(
        callData,
        candideWalletProxy,
        socialRecoveryModule,
        owner,
    )

    # Add third guardian with threshold 2
    callData = socialRecoveryModule.addGuardianWithThreshold.encode_input(
        candideWalletProxy.address, thirdGuardian.address, 2
    )
    ExecuteSocialRecoveryOperation(
        callData,
        candideWalletProxy,
        socialRecoveryModule,
        owner,
    )

    assert socialRecoveryModule.getGuardians(candideWalletProxy.address) == [
        thirdGuardian.address,
        secondGuardian.address,
        firstGuardian.address,
    ]

    callData = socialRecoveryModule.getRecoveryHash(
        candideWalletProxy.address,
        [newOwner1.address],
        1,
        socialRecoveryModule.nonce(candideWalletProxy.address)
        + 1,  # invalid nonce
    )
    g1Sig = firstGuardian.signHash(callData).signature.hex()
    g2Sig = secondGuardian.signHash(callData).signature.hex()
    signatures = [
        [firstGuardian.address, g1Sig],
        [secondGuardian.address, g2Sig],
    ]
    signatures.sort(key=lambda x: int(x[0], 16))
    # Revert if invalid nonce
    try:
        socialRecoveryModule.multiConfirmRecovery(
            candideWalletProxy.address,
            [newOwner1.address],
            1,
            signatures,
            False,
        )
        assert False #hacky way to assert revert
    except Exception as badResponseFormat:
        #this is raising web3.exceptions.BadResponseFormat now !!!
        pass
    # Revert if invalid signatures
    try:
        socialRecoveryModule.multiConfirmRecovery(
            candideWalletProxy.address,
            [newOwner1.address],
            1,
            [[firstGuardian.address, "0x"], [secondGuardian.address, "0x"]],
            False,
        )
        assert False #hacky way to assert revert
    except Exception as badResponseFormat:
        #this is raising web3.exceptions.BadResponseFormat now !!!
        pass

    callData = socialRecoveryModule.getRecoveryHash(
        candideWalletProxy.address,
        [newOwner1.address],
        1,
        socialRecoveryModule.nonce(candideWalletProxy.address),
    )
    g1Sig = firstGuardian.signHash(callData).signature.hex()
    g2Sig = secondGuardian.signHash(callData).signature.hex()
    signatures = [
        [firstGuardian.address, g1Sig],
        [secondGuardian.address, g2Sig],
    ]
    signatures.sort(key=lambda x: int(x[0], 16))
    # Revert if not enough signatures (lower than threshold)
    try:
        socialRecoveryModule.multiConfirmRecovery(
            candideWalletProxy.address,
            [newOwner1.address],
            1,
            [[firstGuardian.address, g1Sig]],
            True,
        )
        assert False #hacky way to assert revert
    except Exception as badResponseFormat:
        #this is raising web3.exceptions.BadResponseFormat now !!!
        pass
    # Revert if new owners array is empty
    try:
        socialRecoveryModule.multiConfirmRecovery(
            candideWalletProxy.address, [], 1, signatures, False
        )
        assert False #hacky way to assert revert
    except Exception as badResponseFormat:
        #this is raising web3.exceptions.BadResponseFormat now !!!
        pass
    # Revert if new threshold of safe is 0
    try:
        socialRecoveryModule.multiConfirmRecovery(
            candideWalletProxy.address,
            [newOwner1.address],
            0,
            signatures,
            False,
        )
        assert False #hacky way to assert revert
    except Exception as badResponseFormat:
        #this is raising web3.exceptions.BadResponseFormat now !!!
        pass

    # Revert if new threshold is higher than new owners count
    try:
        socialRecoveryModule.multiConfirmRecovery(
            candideWalletProxy.address,
            [newOwner1.address],
            2,
            signatures,
            False,
        )
        assert False #hacky way to assert revert
    except Exception as badResponseFormat:
        #this is raising web3.exceptions.BadResponseFormat now !!!
        pass
    # Revert if owner tried to cancel a recovery request while no recovery
    # request exists on chain
    cancelRecoveryCallData = socialRecoveryModule.cancelRecovery.encode_input(
        candideWalletProxy.address
    )
    try:
        ExecuteSocialRecoveryOperation(
            cancelRecoveryCallData,
            candideWalletProxy,
            socialRecoveryModule,
            owner,
        )
        assert False #hacky way to assert revert
    except Exception as badResponseFormat:
        #this is raising web3.exceptions.BadResponseFormat now !!!
        pass

    socialRecoveryModule.multiConfirmRecovery(
        candideWalletProxy.address, [newOwner1.address], 1, signatures, False
    )

    approvals = socialRecoveryModule.getRecoveryApprovals(
        candideWalletProxy.address,
        [newOwner1.address],
        1,
    )

    recoveryRequest = socialRecoveryModule.getRecoveryRequest(
        candideWalletProxy.address
    )

    assert approvals == 2
    assert recoveryRequest[2] == 0

    socialRecoveryModule.executeRecovery(
        candideWalletProxy.address,
        [newOwner1.address],
        1,
    )

    recoveryRequest = socialRecoveryModule.getRecoveryRequest(
        candideWalletProxy.address
    )
    assert recoveryRequest[0] == 2
    assert recoveryRequest[1] == 1
    assert recoveryRequest[2] > 0
    assert recoveryRequest[3] == [newOwner1.address]

    # Owner cancel recovery request
    ExecuteSocialRecoveryOperation(
        cancelRecoveryCallData,
        candideWalletProxy,
        socialRecoveryModule,
        owner,
    )

    callData = socialRecoveryModule.getRecoveryHash(
        candideWalletProxy.address,
        [newOwner1.address],
        1,
        socialRecoveryModule.nonce(candideWalletProxy.address),
    )
    g2Sig = secondGuardian.signHash(callData).signature.hex()
    signatures = [
        [firstGuardian.address, b""],
        [secondGuardian.address, g2Sig],
    ]
    signatures.sort(key=lambda x: int(x[0], 16))

    # Revert if creating recovery request with a null signature while
    # sender is not guardian
    try:
        socialRecoveryModule.multiConfirmRecovery(
            candideWalletProxy.address,
            [newOwner1.address],
            1,
            signatures,
            False,
            {"from": accounts[0]},
        )
        assert False #hacky way to assert revert
    except Exception as badResponseFormat:
        #this is raising web3.exceptions.BadResponseFormat now !!!
        pass

    # Inititate recovery request with supplied null
    # signature if sender is guardian
    firstGuardianAccount = accounts.add(private_key=firstGuardian.key)
    socialRecoveryModule.multiConfirmRecovery(
        candideWalletProxy.address,
        [newOwner1.address],
        1,
        signatures,
        True,
        {"from": firstGuardianAccount},
    )

    # Replace recovery request
    callData = socialRecoveryModule.getRecoveryHash(
        candideWalletProxy.address,
        [newOwner1.address, newOwner2.address],
        2,
        socialRecoveryModule.nonce(candideWalletProxy.address),
    )
    g1Sig = firstGuardian.signHash(callData).signature.hex()
    g2Sig = secondGuardian.signHash(callData).signature.hex()
    g3Sig = thirdGuardian.signHash(callData).signature.hex()
    signatures = [
        [firstGuardian.address, g1Sig],
        [secondGuardian.address, g2Sig],
    ]
    signatures.sort(key=lambda x: int(x[0], 16))

    # Revert because we need at least 3 signatures to replace previous
    # request (because it was only 2 sigs)
    try:
        socialRecoveryModule.multiConfirmRecovery(
            candideWalletProxy.address,
            [newOwner1.address, newOwner2.address],
            2,
            signatures,
            True,
        )
        assert False #hacky way to assert revert
    except Exception as badResponseFormat:
        #this is raising web3.exceptions.BadResponseFormat now !!!
        pass
    signatures = [
        [firstGuardian.address, g1Sig],
        [secondGuardian.address, g2Sig],
        [thirdGuardian.address, g3Sig],
    ]
    signatures.sort(key=lambda x: x[0])

    socialRecoveryModule.multiConfirmRecovery(
        candideWalletProxy.address,
        [newOwner1.address, newOwner2.address],
        2,
        signatures,
        True,
    )

    recoveryRequest = socialRecoveryModule.getRecoveryRequest(
        candideWalletProxy.address
    )
    assert recoveryRequest[0] == 3
    assert recoveryRequest[1] == 2
    assert recoveryRequest[3] == [newOwner1.address, newOwner2.address]

    # Revert if block.timestamp < recoveryRequest.executeAfter
    try:
        socialRecoveryModule.finalizeRecovery(
            candideWalletProxy.address,
        )
        assert False #hacky way to assert revert
    except Exception as badResponseFormat:
        #this is raising web3.exceptions.BadResponseFormat now !!!
        pass

    # simulate time passing in chain
    chain.sleep(2000)
    chain.mine()

    socialRecoveryModule.finalizeRecovery(
        candideWalletProxy.address,
    )

    assert candideWalletProxy.getOwners() == list(
        reversed([newOwner1.address, newOwner2.address])
    )
    assert candideWalletProxy.getThreshold() == 2

    # Test removing 1 owner
    callData = socialRecoveryModule.getRecoveryHash(
        candideWalletProxy.address,
        [newOwner1.address],
        1,
        socialRecoveryModule.nonce(candideWalletProxy.address),
    )
    g1Sig = firstGuardian.signHash(callData).signature.hex()
    g2Sig = secondGuardian.signHash(callData).signature.hex()
    signatures = [
        [firstGuardian.address, g1Sig],
        [secondGuardian.address, g2Sig],
    ]
    signatures.sort(key=lambda x: int(x[0], 16))

    socialRecoveryModule.multiConfirmRecovery(
        candideWalletProxy.address,
        [newOwner1.address],
        1,
        signatures,
        True,
    )

    chain.sleep(2000)
    chain.mine()

    socialRecoveryModule.finalizeRecovery(
        candideWalletProxy.address,
    )

    assert candideWalletProxy.getOwners() == list(
        reversed([newOwner1.address])
    )
    assert candideWalletProxy.getThreshold() == 1

    # Test swapping owner
    callData = socialRecoveryModule.getRecoveryHash(
        candideWalletProxy.address,
        [newOwner3.address],
        1,
        socialRecoveryModule.nonce(candideWalletProxy.address),
    )
    g1Sig = firstGuardian.signHash(callData).signature.hex()
    g2Sig = secondGuardian.signHash(callData).signature.hex()
    signatures = [
        [firstGuardian.address, g1Sig],
        [secondGuardian.address, g2Sig],
    ]
    signatures.sort(key=lambda x: int(x[0], 16))

    socialRecoveryModule.multiConfirmRecovery(
        candideWalletProxy.address,
        [newOwner3.address],
        1,
        signatures,
        True,
    )

    chain.sleep(2000)
    chain.mine()

    socialRecoveryModule.finalizeRecovery(
        candideWalletProxy.address,
    )

    assert candideWalletProxy.getOwners() == list(
        reversed([newOwner3.address])
    )
    assert candideWalletProxy.getThreshold() == 1


# Test using confirmRecovery
def test_confirmRecovery(
    candideWalletProxy, owner, accounts, socialRecoveryModule
):
    firstGuardian = Account.create()
    firstGuardianAccount = accounts.add(private_key=firstGuardian.key)
    secondGuardian = Account.create()
    secondGuardianAccount = accounts.add(private_key=secondGuardian.key)
    thirdGuardian = Account.create()
    thirdGuardianAccount = accounts.add(private_key=thirdGuardian.key)

    # Enable social recovery module for Safe
    callData = candideWalletProxy.enableModule.encode_input(
        socialRecoveryModule.address
    )
    ExecuteExecTransaction(
        candideWalletProxy.address,
        0,
        callData,
        0,
        0,
        0,
        0,
        "0x0000000000000000000000000000000000000000",
        "0x0000000000000000000000000000000000000000",
        owner,
        owner,
        candideWalletProxy,
    )

    assert candideWalletProxy.isModuleEnabled(socialRecoveryModule.address)

    newOwner1 = Account.create()
    newOwner2 = Account.create()
    # newOwner3 = Account.create()

    # Add first guardian
    callData = socialRecoveryModule.addGuardianWithThreshold.encode_input(
        candideWalletProxy.address, firstGuardian.address, 1
    )
    ExecuteSocialRecoveryOperation(
        callData,
        candideWalletProxy,
        socialRecoveryModule,
        owner,
    )

    # Add second guardian
    callData = socialRecoveryModule.addGuardianWithThreshold.encode_input(
        candideWalletProxy.address, secondGuardian.address, 1
    )
    ExecuteSocialRecoveryOperation(
        callData,
        candideWalletProxy,
        socialRecoveryModule,
        owner,
    )

    # Add third guardian with threshold 2
    callData = socialRecoveryModule.addGuardianWithThreshold.encode_input(
        candideWalletProxy.address, thirdGuardian.address, 2
    )
    ExecuteSocialRecoveryOperation(
        callData,
        candideWalletProxy,
        socialRecoveryModule,
        owner,
    )

    assert socialRecoveryModule.getGuardians(candideWalletProxy.address) == [
        thirdGuardian.address,
        secondGuardian.address,
        firstGuardian.address,
    ]

    # revert if sender is not a guardian
    try:
        socialRecoveryModule.confirmRecovery(
            candideWalletProxy.address,
            [newOwner1.address],
            1,
            False,
            {"from": accounts[0]},
        )
        assert False #hacky way to assert revert
    except Exception as badResponseFormat:
        #this is raising web3.exceptions.BadResponseFormat now !!!
        pass

    # revert if execute is True but not enough approvals
    try:
        socialRecoveryModule.confirmRecovery(
            candideWalletProxy.address,
            [newOwner1.address],
            1,
            True,
            {"from": firstGuardianAccount},
        )
        assert False #hacky way to assert revert
    except Exception as badResponseFormat:
        #this is raising web3.exceptions.BadResponseFormat now !!!
        pass

    socialRecoveryModule.confirmRecovery(
        candideWalletProxy.address,
        [newOwner1.address],
        1,
        False,
        {"from": firstGuardianAccount},
    )

    approvals = socialRecoveryModule.getRecoveryApprovals(
        candideWalletProxy.address,
        [newOwner1.address],
        1,
    )

    recoveryRequest = socialRecoveryModule.getRecoveryRequest(
        candideWalletProxy.address
    )

    assert approvals == 1
    assert recoveryRequest[2] == 0

    # multiple confirmRecovery transactions by same guardian
    # won't increase approvals
    socialRecoveryModule.confirmRecovery(
        candideWalletProxy.address,
        [newOwner1.address],
        1,
        False,
        {"from": firstGuardianAccount},
    )

    approvals = socialRecoveryModule.getRecoveryApprovals(
        candideWalletProxy.address,
        [newOwner1.address],
        1,
    )

    assert approvals == 1

    socialRecoveryModule.confirmRecovery(
        candideWalletProxy.address,
        [newOwner1.address],
        1,
        False,
        {"from": secondGuardianAccount},
    )

    approvals = socialRecoveryModule.getRecoveryApprovals(
        candideWalletProxy.address,
        [newOwner1.address],
        1,
    )

    assert approvals == 2

    socialRecoveryModule.executeRecovery(
        candideWalletProxy.address,
        [newOwner1.address],
        1,
    )

    recoveryRequest = socialRecoveryModule.getRecoveryRequest(
        candideWalletProxy.address
    )
    assert recoveryRequest[0] == 2
    assert recoveryRequest[1] == 1
    assert recoveryRequest[2] > 0
    assert recoveryRequest[3] == [newOwner1.address]

    # Owner cancel recovery request
    cancelRecoveryCallData = socialRecoveryModule.cancelRecovery.encode_input(
        candideWalletProxy.address
    )
    ExecuteSocialRecoveryOperation(
        cancelRecoveryCallData,
        candideWalletProxy,
        socialRecoveryModule,
        owner,
    )

    socialRecoveryModule.confirmRecovery(
        candideWalletProxy.address,
        [newOwner1.address],
        1,
        False,
        {"from": firstGuardianAccount},
    )

    socialRecoveryModule.confirmRecovery(
        candideWalletProxy.address,
        [newOwner1.address],
        1,
        True,
        {"from": secondGuardianAccount},
    )

    recoveryRequest = socialRecoveryModule.getRecoveryRequest(
        candideWalletProxy.address
    )
    assert recoveryRequest[0] == 2
    assert recoveryRequest[1] == 1
    assert recoveryRequest[2] > 0
    assert recoveryRequest[3] == [newOwner1.address]

    socialRecoveryModule.confirmRecovery(
        candideWalletProxy.address,
        [newOwner1.address, newOwner2.address],
        2,
        False,
        {"from": firstGuardianAccount},
    )

    # Revert because we need at least 3 signatures to replace
    # previous request (because it was only 2 sigs)
    try:
        socialRecoveryModule.confirmRecovery(
            candideWalletProxy.address,
            [newOwner1.address, newOwner2.address],
            2,
            True,
            {"from": secondGuardianAccount},
        )
        assert False #hacky way to assert revert
    except Exception as badResponseFormat:
        #this is raising web3.exceptions.BadResponseFormat now !!!
        pass

    socialRecoveryModule.confirmRecovery(
        candideWalletProxy.address,
        [newOwner1.address, newOwner2.address],
        2,
        False,
        {"from": secondGuardianAccount},
    )

    socialRecoveryModule.confirmRecovery(
        candideWalletProxy.address,
        [newOwner1.address, newOwner2.address],
        2,
        True,
        {"from": thirdGuardianAccount},
    )

    recoveryRequest = socialRecoveryModule.getRecoveryRequest(
        candideWalletProxy.address
    )
    assert recoveryRequest[0] == 3
    assert recoveryRequest[1] == 2
    assert recoveryRequest[3] == [newOwner1.address, newOwner2.address]


# Test using confirmRecovery and multiConfirmRecovery
def test_multiAndSingleRecovery(
    candideWalletProxy, owner, accounts, socialRecoveryModule
):
    firstGuardian = Account.create()
    # firstGuardianAccount = accounts.add(private_key=firstGuardian.key)
    secondGuardian = Account.create()
    secondGuardianAccount = accounts.add(private_key=secondGuardian.key)
    thirdGuardian = Account.create()
    thirdGuardianAccount = accounts.add(private_key=thirdGuardian.key)

    # Enable social recovery module for Safe
    callData = candideWalletProxy.enableModule.encode_input(
        socialRecoveryModule.address
    )
    ExecuteExecTransaction(
        candideWalletProxy.address,
        0,
        callData,
        0,
        0,
        0,
        0,
        "0x0000000000000000000000000000000000000000",
        "0x0000000000000000000000000000000000000000",
        owner,
        owner,
        candideWalletProxy,
    )

    assert candideWalletProxy.isModuleEnabled(socialRecoveryModule.address)

    newOwner1 = Account.create()
    newOwner2 = Account.create()
    # newOwner3 = Account.create()

    # Add first guardian
    callData = socialRecoveryModule.addGuardianWithThreshold.encode_input(
        candideWalletProxy.address, firstGuardian.address, 1
    )
    ExecuteSocialRecoveryOperation(
        callData,
        candideWalletProxy,
        socialRecoveryModule,
        owner,
    )

    # Add second guardian
    callData = socialRecoveryModule.addGuardianWithThreshold.encode_input(
        candideWalletProxy.address, secondGuardian.address, 1
    )
    ExecuteSocialRecoveryOperation(
        callData,
        candideWalletProxy,
        socialRecoveryModule,
        owner,
    )

    # Add third guardian with threshold 2
    callData = socialRecoveryModule.addGuardianWithThreshold.encode_input(
        candideWalletProxy.address, thirdGuardian.address, 2
    )
    ExecuteSocialRecoveryOperation(
        callData,
        candideWalletProxy,
        socialRecoveryModule,
        owner,
    )

    assert socialRecoveryModule.getGuardians(candideWalletProxy.address) == [
        thirdGuardian.address,
        secondGuardian.address,
        firstGuardian.address,
    ]

    socialRecoveryModule.confirmRecovery(
        candideWalletProxy.address,
        [newOwner1.address],
        1,
        False,
        {"from": thirdGuardianAccount},
    )

    approvals = socialRecoveryModule.getRecoveryApprovals(
        candideWalletProxy.address,
        [newOwner1.address],
        1,
    )

    recoveryRequest = socialRecoveryModule.getRecoveryRequest(
        candideWalletProxy.address
    )

    assert approvals == 1
    assert recoveryRequest[2] == 0

    callData = socialRecoveryModule.getRecoveryHash(
        candideWalletProxy.address,
        [newOwner1.address],
        1,
        socialRecoveryModule.nonce(candideWalletProxy.address),
    )
    g1Sig = firstGuardian.signHash(callData).signature.hex()
    g2Sig = secondGuardian.signHash(callData).signature.hex()
    signatures = [
        [firstGuardian.address, g1Sig],
        [secondGuardian.address, g2Sig],
    ]
    signatures.sort(key=lambda x: int(x[0], 16))

    socialRecoveryModule.multiConfirmRecovery(
        candideWalletProxy.address,
        [newOwner1.address],
        1,
        signatures,
        False,
    )

    approvals = socialRecoveryModule.getRecoveryApprovals(
        candideWalletProxy.address,
        [newOwner1.address],
        1,
    )

    assert approvals == 3

    socialRecoveryModule.executeRecovery(
        candideWalletProxy.address,
        [newOwner1.address],
        1,
    )

    recoveryRequest = socialRecoveryModule.getRecoveryRequest(
        candideWalletProxy.address
    )
    assert recoveryRequest[0] == 3
    assert recoveryRequest[1] == 1
    assert recoveryRequest[2] > 0
    assert recoveryRequest[3] == [newOwner1.address]

    # Owner cancel recovery request
    cancelRecoveryCallData = socialRecoveryModule.cancelRecovery.encode_input(
        candideWalletProxy.address
    )
    ExecuteSocialRecoveryOperation(
        cancelRecoveryCallData,
        candideWalletProxy,
        socialRecoveryModule,
        owner,
    )

    socialRecoveryModule.confirmRecovery(
        candideWalletProxy.address,
        [newOwner1.address, newOwner2.address],
        2,
        False,
        {"from": thirdGuardianAccount},
    )

    callData = socialRecoveryModule.getRecoveryHash(
        candideWalletProxy.address,
        [newOwner1.address, newOwner2.address],
        2,
        socialRecoveryModule.nonce(candideWalletProxy.address),
    )
    g1Sig = firstGuardian.signHash(callData).signature.hex()
    signatures = [
        [firstGuardian.address, g1Sig],
        [secondGuardian.address, b""],
    ]
    signatures.sort(key=lambda x: int(x[0], 16))

    socialRecoveryModule.multiConfirmRecovery(
        candideWalletProxy.address,
        [newOwner1.address, newOwner2.address],
        2,
        signatures,
        True,
        {"from": secondGuardianAccount},
    )

    recoveryRequest = socialRecoveryModule.getRecoveryRequest(
        candideWalletProxy.address
    )
    assert recoveryRequest[0] == 3
    assert recoveryRequest[1] == 2
    assert recoveryRequest[2] > 0
    assert recoveryRequest[3] == [newOwner1.address, newOwner2.address]


def test_erc1271_compatibility(
    candideWalletProxy,
    owner,
    accounts,
    erc1271Wallet,
    erc1271Owner,
    socialRecoveryModule,
):
    erc1271Signer = Account.from_key(erc1271Owner.private_key)
    erc1271InvalidSigner = Account.create()
    secondGuardian = Account.create()

    # Enable social recovery module for Safe
    callData = candideWalletProxy.enableModule.encode_input(
        socialRecoveryModule.address
    )
    ExecuteExecTransaction(
        candideWalletProxy.address,
        0,
        callData,
        0,
        0,
        0,
        0,
        "0x0000000000000000000000000000000000000000",
        "0x0000000000000000000000000000000000000000",
        owner,
        owner,
        candideWalletProxy,
    )

    assert candideWalletProxy.isModuleEnabled(socialRecoveryModule.address)

    # Add first guardian (smart contract wallet)
    callData = socialRecoveryModule.addGuardianWithThreshold.encode_input(
        candideWalletProxy.address, erc1271Wallet.address, 1
    )
    ExecuteSocialRecoveryOperation(
        callData,
        candideWalletProxy,
        socialRecoveryModule,
        owner,
    )

    # Add second guardian
    callData = socialRecoveryModule.addGuardianWithThreshold.encode_input(
        candideWalletProxy.address, secondGuardian.address, 1
    )
    ExecuteSocialRecoveryOperation(
        callData,
        candideWalletProxy,
        socialRecoveryModule,
        owner,
    )

    newOwner1 = Account.create()
    newOwner2 = Account.create()
    newOwner3 = Account.create()

    callData = socialRecoveryModule.getRecoveryHash(
        candideWalletProxy.address,
        [newOwner1.address, newOwner2.address, newOwner3.address],
        3,
        socialRecoveryModule.nonce(candideWalletProxy.address),
    )
    sig1271 = erc1271Signer.signHash(callData).signature.hex()
    invalidSig1271 = erc1271InvalidSigner.signHash(callData).signature.hex()
    g2Sig = secondGuardian.signHash(callData).signature.hex()
    signatures = [
        [erc1271Wallet.address, invalidSig1271],
        [secondGuardian.address, g2Sig],
    ]
    signatures.sort(key=lambda x: int(x[0], 16))

    # revert because invalid 1271 signature
    try:
        socialRecoveryModule.multiConfirmRecovery(
            candideWalletProxy.address,
            [newOwner1.address, newOwner2.address, newOwner3.address],
            3,
            signatures,
            False,
        )
        assert False #hacky way to assert revert
    except Exception as badResponseFormat:
        #this is raising web3.exceptions.BadResponseFormat now !!!
        pass

    signatures = [
        [erc1271Wallet.address, sig1271],
        [secondGuardian.address, g2Sig],
    ]
    signatures.sort(key=lambda x: int(x[0], 16))

    socialRecoveryModule.multiConfirmRecovery(
        candideWalletProxy.address,
        [newOwner1.address, newOwner2.address, newOwner3.address],
        3,
        signatures,
        True,
    )

    recoveryRequest = socialRecoveryModule.getRecoveryRequest(
        candideWalletProxy.address
    )
    assert recoveryRequest[0] == 2
    assert recoveryRequest[1] == 3
    assert recoveryRequest[3] == [
        newOwner1.address,
        newOwner2.address,
        newOwner3.address,
    ]

    # simulate time passing in chain
    chain.sleep(2000)
    chain.mine()

    socialRecoveryModule.finalizeRecovery(
        candideWalletProxy.address,
    )

    assert candideWalletProxy.getOwners() == list(
        reversed([newOwner1.address, newOwner2.address, newOwner3.address])
    )
    assert candideWalletProxy.getThreshold() == 3
