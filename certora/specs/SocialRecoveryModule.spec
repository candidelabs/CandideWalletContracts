using SafeHarness as safeContract;
using GuardianStorageHarness as guardianStorageContract;

definition SENTINEL() returns address = 1;

methods {
    // Social Recovery Module Functions
    function isGuardian(address, address) external returns (bool) envfree;
    function guardiansCount(address) external returns (uint256) envfree;
    function threshold(address) external returns (uint256) envfree;
    function nonce(address) external returns (uint256) envfree;
    function getRecoveryHash(address, address[], uint256, uint256) external returns (bytes32) envfree;
    function getRecoveryApprovals(address, address[], uint256) external returns (uint256) envfree;
    function hasGuardianApproved(address, address, address[], uint256) external returns (bool) envfree;

    // Guardian Storage Functions
    function guardianStorageContract.countGuardians(address) external returns (uint256) envfree;
    function guardianStorageContract.getGuardians(address) external returns (address[]) envfree;

    // Safe Functions
    function safeContract.isModuleEnabled(address module) external returns (bool) envfree;
    function safeContract.isOwner(address owner) external returns (bool) envfree;
    function safeContract.getOwners() external returns (address[] memory) envfree;
    function safeContract.getThreshold() external returns (uint256) envfree;

    // Wildcard Functions
    function _.execTransactionFromModule(address to, uint256 value, bytes data, Enum.Operation operation) external with (env e) => summarizeSafeExecTransactionFromModule(calledContract, e, to, value, data, operation) expect bool ALL;
    function _.isModuleEnabled(address module) external => DISPATCHER(false);
    function _.isOwner(address owner) external => DISPATCHER(false);
    function _.getOwners() external => DISPATCHER(false);
    function _._ external => DISPATCH[] default NONDET;
}

ghost mapping(address => mathint) ghostNewThreshold {
    init_state axiom forall address account. ghostNewThreshold[account] == 0;
}
hook Sload uint256 value recoveryRequests[KEY address account].newThreshold {
    require ghostNewThreshold[account] == to_mathint(value);
}
hook Sstore recoveryRequests[KEY address account].newThreshold uint256 value {
    ghostNewThreshold[account] = value;
}

ghost mapping(address => mathint) ghostNewOwnersLength {
    init_state axiom forall address account. ghostNewOwnersLength[account] == 0;
}
hook Sload uint256 value recoveryRequests[KEY address account].newOwners.length {
    require ghostNewOwnersLength[account] == to_mathint(value);
}
hook Sstore recoveryRequests[KEY address account].newOwners.length uint256 value {
    ghostNewOwnersLength[account] = value;
}

// A summary function that helps the prover resolve calls to `safeContract`.
function summarizeSafeExecTransactionFromModule(address callee, env e, address to, uint256 value, bytes data, Enum.Operation operation) returns bool {
    if (callee == safeContract) {
        return safeContract.execTransactionFromModule(e, to, value, data, operation);
    }
    return _;
}

// A setup function that requires Safe contract to enable the Social Recovery Module.
function requireSocialRecoveryModuleEnabled() {
    require(safeContract.isModuleEnabled(currentContract));
}

// Setup function that `require`s the integrity of the guardians linked list
// in the `GuardianStorage` contract. This is needed as `invariant`s can only
// be proven for `currentContract` and not `guardianStorageContract`, however,
// the integrity of this list is required for rules and invariants of the
// recovery module. For proof of this integrity, see `GuardianStorage.spec`.
function requireGuardiansLinkedListIntegrity(address guardian) {
    uint256 index;
    require index < guardianStorageContract.entries[safeContract].count;
    require currentContract.isGuardian(safeContract, guardian) =>
        guardianStorageContract.getGuardians(safeContract)[index] == guardian;
    require !currentContract.isGuardian(safeContract, guardian) =>
        (forall address prevGuardian. guardianStorageContract.entries[safeContract].guardians[prevGuardian] != guardian);
    require guardianStorageContract.entries[safeContract].count == guardianStorageContract.countGuardians(safeContract);
}

// Invariant that proves the relationship between the new threshold, new owner length and the
// `confirmedHash`. If there is a `confirmedHash` for a given `hash` and `guardian`, then the
// threshold should be greater than zero and less than or equal to the number of new owners.
invariant approvedHashesHaveCorrectThreshold(address wallet, address[] newOwners, uint256 newThreshold, uint256 nonce, bytes32 hash)
    hash == getRecoveryHash(wallet, newOwners, newThreshold, nonce) &&
    (exists address guardian. currentContract.confirmedHashes[hash][guardian]) =>
        0 < newThreshold && newThreshold <= newOwners.length
    filtered {
        f -> f.contract != safeContract
    }

// Invariant that proves the relationship between the new threshold and the owner.
// Depending on the recovery cycle, there could be no new owners present in the 
// recoveryRequest, or not. One thing is certain, the threshold should always be
// less than or equal to the number of new owners.
invariant thresholdIsAlwaysLessThanEqGuardiansCount(address account)
    (ghostNewOwnersLength[account] == 0 => ghostNewThreshold[account] == 0) &&
    (ghostNewOwnersLength[account] > 0 => ghostNewThreshold[account] > 0) &&
    ghostNewThreshold[account] <= ghostNewOwnersLength[account]
    filtered {
        f -> f.contract != safeContract
    }
{
    preserved executeRecovery(address wallet, address[] newOwners, uint256 newThreshold) with (env e) {
        uint256 nonce = currentContract.nonce(wallet);
        bytes32 hash = getRecoveryHash(wallet, newOwners, newThreshold, nonce);
        requireInvariant approvedHashesHaveCorrectThreshold(wallet, newOwners, newThreshold, nonce, hash);
    }
}

// This integrity rule verifies that if the addGuardianWithThreshold(...) executes, then ensure that:
// - the Social Recovery Module is enabled
// - the caller to the Module has to be the Safe Contract
// - the new guardian is added to the guardian list,
// - and no other account (guardian or not) is affected.
rule addGuardianWorksAsExpected(env e, address guardian, uint256 threshold, address otherAccount) {
    requireGuardiansLinkedListIntegrity(guardian);

    // If threshold is same as before, then no change is made to the threshold during guardian addition.
    // Thus, it is required to add this check to ensure no initial state have threshold > count.
    require threshold == guardianStorageContract.entries[safeContract].threshold =>
        guardianStorageContract.entries[safeContract].threshold <= guardianStorageContract.entries[safeContract].count;

    uint256 currentGuardiansCount = guardianStorageContract.entries[safeContract].count;
    bool otherAccountIsGuardian = currentContract.isGuardian(safeContract, otherAccount);

    currentContract.addGuardianWithThreshold(e, safeContract, guardian, threshold);

    assert safeContract.isModuleEnabled(currentContract);
    assert e.msg.sender == safeContract;
    assert currentContract.isGuardian(safeContract, guardian);
    assert guardian != otherAccount => otherAccountIsGuardian == currentContract.isGuardian(safeContract, otherAccount);
    assert currentGuardiansCount + 1 == to_mathint(guardianStorageContract.entries[safeContract].count);
    assert threshold > 0 && threshold <= guardianStorageContract.entries[safeContract].count;
}

// This integrity rule verifies that the guardian can always be added considering ideal conditions.
rule guardianCanAlwaysBeAdded(env e, address guardian, uint256 threshold) {
    requireSocialRecoveryModuleEnabled();
    requireGuardiansLinkedListIntegrity(guardian);

    // No value should be sent with the transaction.
    require e.msg.value == 0;

    uint256 currentGuardiansCount = guardianStorageContract.entries[safeContract].count;    
    // The guardian count should be less than the maximum value to prevent overflow.
    require currentGuardiansCount < max_uint256; // To prevent overflow (Realistically can't reach).

    // The guardian should not be values such as zero, sentinel, or the Safe contract itself.
    require guardian != 0;
    require guardian != SENTINEL();
    require guardian != safeContract;

    // The guardian should not be an owner of the Safe contract at the time of addition.
    require !safeContract.isOwner(guardian);
    // The guardian should not be already added as a guardian.
    require !currentContract.isGuardian(safeContract, guardian);

    // The threshold must be greater than 0 and less than or equal to the total number of guardians after adding the new guardian.
    require threshold > 0 && to_mathint(threshold) <= guardianStorageContract.entries[safeContract].count + 1;

    // Safe contract should be the sender of the transaction.
    require e.msg.sender == safeContract;
    currentContract.addGuardianWithThreshold@withrevert(e, safeContract, guardian, threshold);
    bool isReverted = lastReverted;

    assert !isReverted &&
        currentContract.isGuardian(safeContract, guardian) &&
        currentGuardiansCount + 1 == to_mathint(guardianStorageContract.entries[safeContract].count);
}

// This integrity rule verifies the possibilites in which the addition of a new guardian can revert.
rule addGuardianRevertPossibilities(env e, address guardian, uint256 threshold) {
    bool isGuardian = currentContract.isGuardian(safeContract, guardian);

    currentContract.addGuardianWithThreshold@withrevert(e, safeContract, guardian, threshold);
    bool isReverted = lastReverted;

    assert isReverted =>
        isGuardian ||
        e.msg.sender != safeContract ||
        e.msg.value != 0 ||
        guardian == 0 ||
        guardian == SENTINEL() ||
        guardian == safeContract ||
        safeContract.isOwner(guardian) ||
        threshold == 0 ||
        to_mathint(threshold) > guardianStorageContract.entries[safeContract].count + 1 ||
        guardianStorageContract.entries[safeContract].count == max_uint256 ||
        !safeContract.isModuleEnabled(currentContract);
}

// This integrity rule verifies that if the revokeGuardianWithThreshold(...) executes, then ensure that:
// - the Social Recovery Module is enabled
// - the caller to the Module has to be the Safe Contract
// - the guardian is revoked from the guardian list
// - the linked list integrity remains,
// - and no other account (guardian or not) is affected.
rule revokeGuardiansWorksAsExpected(env e, address guardian, address prevGuardian, uint256 threshold, address otherAccount) {
    requireGuardiansLinkedListIntegrity(guardian);

    address nextGuardian = guardianStorageContract.entries[safeContract].guardians[guardian];
    bool otherAccountIsGuardian = currentContract.isGuardian(safeContract, otherAccount);

    uint256 currentGuardiansCount = guardianStorageContract.entries[safeContract].count;

    currentContract.revokeGuardianWithThreshold(e, safeContract, prevGuardian, guardian, threshold);

    assert safeContract.isModuleEnabled(currentContract);
    assert e.msg.sender == safeContract;
    assert !currentContract.isGuardian(safeContract, guardian);
    assert guardianStorageContract.entries[safeContract].guardians[prevGuardian] == nextGuardian;
    assert guardian != otherAccount => otherAccountIsGuardian == currentContract.isGuardian(safeContract, otherAccount);
    assert currentGuardiansCount - 1 == to_mathint(guardianStorageContract.entries[safeContract].count);
    assert threshold <= guardianStorageContract.entries[safeContract].count;
}

// This integrity rule verifies that the guardian can always be revoked considering ideal conditions.
rule guardianCanAlwaysBeRevoked(env e, address guardian, address prevGuardian, uint256 threshold) {
    requireSocialRecoveryModuleEnabled();
    requireGuardiansLinkedListIntegrity(guardian);

    // No value should be sent with the transaction.
    require e.msg.value == 0;
    // If new threshold is 0, then you must be removing the last guardian meaning the guardian count should be 1.
    require threshold == 0 => guardianStorageContract.entries[safeContract].count == 1;
    // The new threshold should be less than or equal to the guardian count after removing.
    require to_mathint(threshold) <= guardianStorageContract.entries[safeContract].count - 1;
    // The address should be a guardian.
    require currentContract.isGuardian(safeContract, guardian);

    address nextGuardian = guardianStorageContract.entries[safeContract].guardians[guardian];
    require guardianStorageContract.entries[safeContract].guardians[prevGuardian] == guardian;

    uint256 currentGuardiansCount = guardianStorageContract.entries[safeContract].count;    

    // Safe Contract should be the sender of the transaction.
    require e.msg.sender == safeContract;
    currentContract.revokeGuardianWithThreshold@withrevert(e, safeContract, prevGuardian, guardian, threshold);
    bool isReverted = lastReverted;

    assert !isReverted &&
        guardianStorageContract.entries[safeContract].guardians[prevGuardian] == nextGuardian &&
        !currentContract.isGuardian(safeContract, guardian) &&
        currentGuardiansCount - 1 == to_mathint(guardianStorageContract.entries[safeContract].count);
}

// This integrity rule verifies the possibilites in which the revocation of a new guardian can revert.
rule revokeGuardianRevertPossibilities(env e, address prevGuardian, address guardian, uint256 threshold) {
    requireGuardiansLinkedListIntegrity(guardian);

    bool isGuardian = currentContract.isGuardian(safeContract, guardian);

    currentContract.revokeGuardianWithThreshold@withrevert(e, safeContract, prevGuardian, guardian, threshold);
    bool isReverted = lastReverted;

    assert isReverted =>
        !isGuardian ||
        e.msg.sender != safeContract ||
        e.msg.value != 0 ||
        !safeContract.isModuleEnabled(currentContract) ||
        guardianStorageContract.entries[safeContract].guardians[prevGuardian] != guardian ||
        to_mathint(threshold) > guardianStorageContract.entries[safeContract].count - 1 ||
        (threshold == 0 && guardianStorageContract.entries[safeContract].count != 1);
}

// This rule verifies that the guardian can always initiate recovery considering some ideal conditions.
rule confirmRecoveryCanAlwaysBeInitiatedByGuardian(env e, address guardian, address[] newOwners, uint256 newThreshold, bool execute) {
    uint256 index;
    // Index must be valid.
    require index < newOwners.length;

    // The threshold should always be greater than 0 and less than the number of new owners.
    require newThreshold > 0;
    require newThreshold <= newOwners.length;

    // No ether should be sent as part of this function call, and the caller should be a guardian.
    require e.msg.value == 0;
    require e.msg.sender == guardian;
    require currentContract.isGuardian(safeContract, guardian);

    requireGuardiansLinkedListIntegrity(guardian);

    // Nonce and timestamp + recovery period should not overflow (Realistically can't reach).
    require e.block.timestamp + currentContract.recoveryPeriod <= max_uint64;
    uint256 nonce = currentContract.nonce(safeContract);
    require nonce < max_uint256;

    bytes32 recoveryHash = currentContract.getRecoveryHash(safeContract, newOwners, newThreshold, nonce);
    // This ensures that the recovery is not already initiated.
    require currentContract.recoveryRequests[safeContract].executeAfter == 0;

    // This ensures that the required threshold is reached.
    require currentContract.getRecoveryApprovals(safeContract, newOwners, newThreshold) == currentContract.threshold(safeContract);

    currentContract.confirmRecovery@withrevert(e, safeContract, newOwners, newThreshold, execute);
    bool isReverted = lastReverted;

    assert !isReverted &&
        currentContract.confirmedHashes[recoveryHash][e.msg.sender];
    assert execute =>
        to_mathint(currentContract.recoveryRequests[safeContract].executeAfter) == e.block.timestamp + currentContract.recoveryPeriod &&
        currentContract.recoveryRequests[safeContract].newThreshold == newThreshold &&
        currentContract.recoveryRequests[safeContract].newOwners.length == newOwners.length &&
        currentContract.recoveryRequests[safeContract].newOwners[index] == newOwners[index];
}

// This rule verifies that the finalization cannot happen if the recovery module is not enabled.
// Exceptions are made for the case where the Safe has only one owner and the recovery is initiated
// - with zero new owners and zero as the new threshold
// - with same last owner & threshold as Safe.
rule disabledRecoveryModuleResultsInFinalizationRevert(env e) {
    address[] ownersBefore = safeContract.getOwners();
    uint256 currentThreshold = safeContract.getThreshold();

    require !safeContract.isModuleEnabled(currentContract);

    currentContract.finalizeRecovery@withrevert(e, safeContract);
    bool isReverted = lastReverted;

    // If the recovery finalization is initiated with the safe having only one owner,
    // and the finalize recovery initiated with no new owners and zero as new threshold,
    // OR with the same last owner of safe and threshold == newThreshold == 1,
    // then the finalize recovery call goes through, as no owner is removed and no new
    // owner is added. Though it is not possible to have a recovery initiation with zero
    // owners.
    assert isReverted ||
        (ownersBefore[0] == safeContract.getOwners()[0] &&
            safeContract.getOwners().length == 1 &&
            currentThreshold == safeContract.getThreshold());
}

// This rule verifies that a guardian can only initiate recovery for the safe account it has been assigned to.
// Here we only check initiation, and not execution of recovery.
rule guardiansCanInitiateRecoveryForAssignedAccount(env e, address guardian, address[] newOwners, uint256 newThreshold) {
    requireGuardiansLinkedListIntegrity(guardian);

    require e.msg.sender == guardian;
    require e.msg.value == 0;
    require newOwners.length > 0;
    require newThreshold > 0 && newThreshold <= newOwners.length;
    // This is required as FV might have a value beyond 2^160 for address in the newOwners.
    require forall uint256 i. 0 <= i && i < newOwners.length => to_mathint(newOwners[i]) < 2^160;

    // The guardian can call the confirmRecovery twice with the same parameters, thus we check if the guardian had
    // already confirmed the recovery.
    bool guardianConfirmed = currentContract.hasGuardianApproved(safeContract, guardian, newOwners, newThreshold);
    uint256 currentApprovals = currentContract.getRecoveryApprovals(safeContract, newOwners, newThreshold);

    // Here we are only focusing on the initiation and not the execution of the recovery, thus execute
    // parameter is passed as false.
    currentContract.confirmRecovery@withrevert(e, safeContract, newOwners, newThreshold, false);
    bool isReverted = lastReverted;

    // This checks the guardian cannot initiate recovery for account not assigned by safe account.
    assert isReverted => !currentContract.isGuardian(safeContract, guardian);
    // This checks if recovery initiated, then the caller was a guardian of that safe account and has
    // successfully initiated the process.
    assert !isReverted =>
        currentContract.isGuardian(safeContract, guardian) &&
        currentContract.hasGuardianApproved(safeContract, guardian, newOwners, newThreshold) &&
        (guardianConfirmed || to_mathint(currentContract.getRecoveryApprovals(safeContract, newOwners, newThreshold)) == currentApprovals + 1);
}

// Recovery can be cancelled
rule cancelRecovery(env e) {
    require e.msg.sender == safeContract;
    require e.msg.value == 0;

    // A recovery request must be initiated.
    require currentContract.recoveryRequests[safeContract].executeAfter > 0;
    require currentContract.walletsNonces[safeContract] > 0;

    currentContract.cancelRecovery@withrevert(e, safeContract);
    assert !lastReverted;
}

// Cancelling recovery for a wallet does not affect other wallets
rule cancelRecoveryDoesNotAffectOtherWallet(env e, address otherWallet) {
    require e.msg.sender == safeContract;
    require e.msg.value == 0;

    SocialRecoveryModule.RecoveryRequest otherRequestBefore = currentContract.getRecoveryRequest(e, otherWallet);
    uint256 otherWalletNonceBefore = currentContract.walletsNonces[otherWallet];
    uint256 i;
    require i < otherRequestBefore.newOwners.length;

    // A recovery request must be initiated.
    require currentContract.recoveryRequests[safeContract].executeAfter > 0;
    require currentContract.walletsNonces[safeContract] > 0;

    currentContract.cancelRecovery(e, safeContract);

    SocialRecoveryModule.RecoveryRequest otherRequestAfter = currentContract.getRecoveryRequest(e, otherWallet);

    assert safeContract != otherWallet =>
        otherRequestBefore.guardiansApprovalCount == otherRequestAfter.guardiansApprovalCount &&
        otherRequestBefore.newThreshold == otherRequestAfter.newThreshold &&
        otherRequestBefore.executeAfter == otherRequestAfter.executeAfter &&
        otherRequestBefore.newOwners.length == otherRequestAfter.newOwners.length &&
        otherRequestBefore.newOwners[i] == otherRequestAfter.newOwners[i] &&
        otherWalletNonceBefore == currentContract.walletsNonces[otherWallet];
}

rule recoveryFinalisation(env e) {
    address[] ownersBefore = safeContract.getOwners();
    uint ownersBeforeCount;

    address[] newOwners;
    uint newOwnersCount;
    // x represents any arbitrary index of newOwners[].
    uint x;

    require currentContract.recoveryRequests[safeContract].newOwners.length > 0;
    require newOwnersCount == currentContract.recoveryRequests[safeContract].newOwners.length;
    require x < newOwnersCount;

    require forall uint256 i. 0 <= i && i < newOwnersCount => newOwners[i] == currentContract.recoveryRequests[safeContract].newOwners[i];

    require ownersBefore.length > 0;
    require ownersBeforeCount < ownersBefore.length;
    require ownersBefore[ownersBeforeCount] != 0 && ownersBefore[ownersBeforeCount] != 1; 
    require currentContract.recoveryRequests[safeContract].executeAfter > 0;
    require to_mathint(e.block.timestamp) > to_mathint(currentContract.recoveryRequests[safeContract].executeAfter);
    
    finalizeRecovery@withrevert(e, safeContract);
    bool isLastReverted = lastReverted;

    address[] ownersAfter = safeContract.getOwners();
    assert !isLastReverted => ownersAfter.length == newOwnersCount;
    assert !isLastReverted => ownersAfter[x] == newOwners[x];
}
