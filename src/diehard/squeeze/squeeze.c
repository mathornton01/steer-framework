// =================================================================================================
//! @file squeeze.c
//! @author STEER Framework Contributors
//! @brief This file implements the Diehard Squeeze test for the STEER framework.
//! @remarks Requires ANSI C99 (or better) compliant compilers.
//! @remarks Supported host operating systems: Any *nix
//! @copyright Copyright (c) 2024 Anametric, Inc. All rights reserved.
//!
//  Includes
// =================================================================================================
#include "steer.h"
#include "steer_json_utilities.h"
#include "steer_nist_sts_utilities_private.h"
#include "steer_parameters_info_utilities.h"
#include "steer_report_utilities.h"
#include "steer_report_utilities_private.h"
#include "steer_string_utilities.h"
#include "steer_string_utilities_private.h"
#include "steer_test_info_utilities.h"
#include "steer_test_shell.h"
#include "steer_utilities.h"
#include "steer_utilities_private.h"
#include "steer_value_utilities.h"
#include "cephes.h"
#include "defs.h"
#include <math.h>
#include <stdlib.h>
#include <string.h>

// =================================================================================================
//  Private constants
// =================================================================================================

#define PROGRAM_NAME        "diehard_squeeze_test"
#define PROGRAM_VERSION     "0.1.0"
#define TEST_NAME           "squeeze"
#define TEST_DESCRIPTION \
"The Squeeze test starts with k = 2^31 and repeatedly multiplies by a random uniform \
value in (0,1) until k reaches 1. The number of iterations is recorded. This process \
is repeated for many trials, and the distribution of iteration counts is compared \
against the theoretical distribution using a chi-squared test. The test is sensitive \
to generators with poor multiplicative structure."
#define CONFIGURATION_COUNT         1
#define DIEHARD_NAME                "Diehard Statistical Test Battery"

#define MINIMUM_BITSTREAM_COUNT     1
#define MINIMUM_BITSTREAM_LENGTH    262144
#define MINIMUM_SIGNIFICANCE_LEVEL  0.0
#define MAXIMUM_SIGNIFICANCE_LEVEL  1.0

#define SQUEEZE_NUM_BINS            43
#define SQUEEZE_BIN_OFFSET          6       // bin 0 corresponds to <=6

// =================================================================================================
//  Private types
// =================================================================================================

typedef struct tdiehard_squeezeprivatedata
{
    tSTEER_CliArguments*        cliArguments;
    tSTEER_ReportPtr            report;
    uint64_t                    bitstreamCount;
    uint64_t                    bitstreamLength;
    double                      significanceLevel;
    uint32_t                    significanceLevelPrecision;
    uint64_t                    minimumTestCountRequiredForSignificance;
    uint64_t                    predictedPassedTestCount;
    uint64_t                    predictedFailedTestCount;
    tSTEER_ConfigurationState   configurationState[CONFIGURATION_COUNT];
    uint64_t                    ones;
    uint64_t                    zeros;
    double                      chiSquared;
    int32_t                     numTrials;
    double                      probabilityValue;
}
tDiehard_SqueezePrivateData;

// =================================================================================================
//  Private globals
// =================================================================================================

static tSTEER_InfoList gReferences = {
    2,
    {
        "George Marsaglia, The Marsaglia Random Number CDROM, 1995",
        "George Marsaglia, DIEHARD: A Battery of Tests of Randomness, 1996"
    }
};

static tSTEER_InfoList gAuthors = {
    1,
    {
        "George Marsaglia"
    }
};

static tSTEER_InfoList gContributors = {
    1,
    {
        STEER_CONTRIBUTOR_GARY_WOODCOCK
    }
};

static tSTEER_InfoList gMaintainers = {
    2,
    {
        STEER_MAINTAINER_ANAMETRIC,
        STEER_MAINTAINER_SMU_DARWIN_DEASON
    }
};

static tSTEER_TestInfo gTestInfo = {
    TEST_NAME,
    DIEHARD_NAME,
    TEST_DESCRIPTION,
    eSTEER_Complexity_Average,
    &gReferences,
    PROGRAM_NAME,
    PROGRAM_VERSION,
    eSTEER_InputFormat_Bitstream,
    STEER_REPOSITORY_URI,
    &gAuthors,
    &gContributors,
    &gMaintainers,
    STEER_CONTACT
};

static tSTEER_ParameterInfoList gParameterInfoList = {
    3,
    {
        {
            STEER_JSON_TAG_BITSTREAM_COUNT,
            STEER_JSON_VALUE_UNSIGNED_64_BIT_INTEGER,
            NULL,
            STEER_JSON_VALUE_BITSTREAMS,
            "1",
            "1",
            NULL
        },
        {
            STEER_JSON_TAG_BITSTREAM_LENGTH,
            STEER_JSON_VALUE_UNSIGNED_64_BIT_INTEGER,
            NULL,
            STEER_JSON_VALUE_BITS,
            "1000000",
            "262144",
            NULL
        },
        {
            STEER_JSON_TAG_SIGNIFICANCE_LEVEL,
            STEER_JSON_VALUE_DOUBLE_PRECISION_FLOATING_POINT,
            STEER_JSON_VALUE_DEFAULT_FLOATING_POINT_PRECISION,
            NULL,
            STEER_JSON_VALUE_DEFAULT_SIGNIFICANCE_LEVEL,
            STEER_JSON_VALUE_MINIMUM_SIGNIFICANCE_LEVEL,
            STEER_JSON_VALUE_MAXIMUM_SIGNIFICANCE_LEVEL
        }
    }
};

static tSTEER_ParametersInfo gParametersInfo = {
    TEST_NAME,
    &gParameterInfoList
};

// =================================================================================================
//  Expected proportions for 1000 trials (Marsaglia)
//  Bins: index 0 = <=6, index 1 = 7, ..., index 41 = 47, index 42 = >=48
// =================================================================================================
static const double gExpectedProportions[SQUEEZE_NUM_BINS] = {
    0.00000000, 0.00000000, 0.00000000, 0.00000000, 0.00000000, 0.00000000,
    0.00000002, 0.00000029, 0.00000386, 0.00004277, 0.00040132, 0.00319510,
    0.02157828, 0.12388050, 0.60252100, 2.47402800, 8.55083500, 24.6860700,
    58.8612900, 114.550200, 178.762600, 218.760600, 203.827500, 141.395300,
    71.4450700, 25.5471400, 6.33385100, 1.06951400, 0.12111630, 0.00909044,
    0.00044797, 0.00001425, 0.00000029, 0.00000000, 0.00000000, 0.00000000,
    0.00000000, 0.00000000, 0.00000000, 0.00000000, 0.00000000, 0.00000000,
    0.00000000
};

// =================================================================================================
//  Helper: extract a 32-bit unsigned integer from bitstream
// =================================================================================================
static uint32_t ExtractUint32(uint8_t* buffer, uint64_t bitOffset)
{
    uint32_t value = 0;
    int i;
    for (i = 0; i < 32; i++)
        value = (value << 1) | buffer[bitOffset + i];
    return value;
}

// =================================================================================================
//  RunTest
// =================================================================================================
int32_t RunTest(tDiehard_SqueezePrivateData* privateData,
                uint8_t* bitstreamBuffer,
                bool* passed)
{
    int32_t result = STEER_RESULT_SUCCESS;
    int32_t observed[SQUEEZE_NUM_BINS];
    double expected[SQUEEZE_NUM_BINS];
    uint64_t totalBits = privateData->bitstreamLength;
    uint64_t bitPos = 0;
    int32_t nTrials = 0;
    double chiSquared = 0.0;
    int df = 0;
    int i;

    memset(observed, 0, sizeof(observed));

    // Run as many trials as bits allow
    while (bitPos + 32 <= totalBits)
    {
        double k = 2147483648.0;    // 2^31
        int iterations = 0;

        while (k > 1.0 && (bitPos + 32 <= totalBits))
        {
            uint32_t raw = ExtractUint32(bitstreamBuffer, bitPos);
            bitPos += 32;
            // Convert to uniform (0,1): add 0.5 to avoid exact 0
            double u = ((double)raw + 0.5) / 4294967296.0;
            k = ceil(k * u);
            iterations++;
        }

        // Only count trial if squeeze completed (k reached 1)
        if (k <= 1.0)
        {
            nTrials++;
            // Categorize: bin 0 = <=6, bin 1 = 7, ..., bin 41 = 47, bin 42 = >=48
            int bin;
            if (iterations <= 6)
                bin = 0;
            else if (iterations >= 48)
                bin = SQUEEZE_NUM_BINS - 1;
            else
                bin = iterations - 6;   // 7->1, 8->2, ..., 47->41

            observed[bin]++;
        }
    }

    privateData->numTrials = nTrials;

    if (nTrials == 0)
    {
        privateData->chiSquared = 0.0;
        privateData->probabilityValue = 0.0;
        *passed = false;
        return result;
    }

    // Scale expected frequencies from 1000 trials to nTrials
    for (i = 0; i < SQUEEZE_NUM_BINS; i++)
        expected[i] = gExpectedProportions[i] * ((double)nTrials / 1000.0);

    // Compute chi-squared statistic over bins with expected > 0
    chiSquared = 0.0;
    df = 0;
    for (i = 0; i < SQUEEZE_NUM_BINS; i++)
    {
        if (expected[i] > 0.0)
        {
            double diff = (double)observed[i] - expected[i];
            chiSquared += (diff * diff) / expected[i];
            df++;
        }
    }
    df--;   // degrees of freedom = number of non-zero bins - 1

    privateData->chiSquared = chiSquared;

    // P-value using upper incomplete gamma function
    if (df > 0)
        privateData->probabilityValue = cephes_igamc((double)df / 2.0, chiSquared / 2.0);
    else
        privateData->probabilityValue = 0.0;

    *passed = (privateData->probabilityValue >= privateData->significanceLevel);
    return result;
}

// =================================================================================================
//  GetTestInfo
// =================================================================================================
char* GetTestInfo(void)
{
    char* json = NULL;
    int32_t result = STEER_TestInfoToJson(&gTestInfo, &json);
    if (result == STEER_RESULT_SUCCESS)
        return json;
    else
        return NULL;
}

// =================================================================================================
//  GetParametersInfo
// =================================================================================================
char* GetParametersInfo(void)
{
    char* json = NULL;
    int32_t result = STEER_ParametersInfoToJson(&gParametersInfo, &json);
    if (result == STEER_RESULT_SUCCESS)
        return json;
    else
        return NULL;
}

// =================================================================================================
//  InitTest
// =================================================================================================
int32_t InitTest(tSTEER_CliArguments* cliArguments,
                 tSTEER_ParameterSet* parameters,
                 void** testPrivateData,
                 uint64_t* bufferSizeInBytes)
{
    int32_t result = STEER_RESULT_SUCCESS;
    tDiehard_SqueezePrivateData* privData = NULL;

    *testPrivateData = NULL;
    *bufferSizeInBytes = 0;

    result = STEER_AllocateMemory(sizeof(tDiehard_SqueezePrivateData), (void**)&privData);

    if (result == STEER_RESULT_SUCCESS)
    {
        uint_fast32_t i = 0;
        void* nativeValue = NULL;

        privData->cliArguments = cliArguments;

        for (i = 0; i < parameters->count; i++)
        {
            if (strcmp(parameters->parameter[i].name, STEER_JSON_TAG_BITSTREAM_COUNT) == 0)
            {
                result = STEER_GetNativeValue(parameters->parameter[i].dataType,
                                              parameters->parameter[i].value, &nativeValue);
                if (result == STEER_RESULT_SUCCESS)
                {
                    privData->bitstreamCount = *((uint64_t*)nativeValue);
                    STEER_FreeMemory(&nativeValue);
                }
            }
            else if (strcmp(parameters->parameter[i].name, STEER_JSON_TAG_BITSTREAM_LENGTH) == 0)
            {
                result = STEER_GetNativeValue(parameters->parameter[i].dataType,
                                              parameters->parameter[i].value, &nativeValue);
                if (result == STEER_RESULT_SUCCESS)
                {
                    privData->bitstreamLength = *((uint64_t*)nativeValue);
                    STEER_FreeMemory(&nativeValue);
                }
            }
            else if (strcmp(parameters->parameter[i].name, STEER_JSON_TAG_SIGNIFICANCE_LEVEL) == 0)
            {
                result = STEER_GetNativeValue(parameters->parameter[i].dataType,
                                              parameters->parameter[i].value, &nativeValue);
                if (result == STEER_RESULT_SUCCESS)
                {
                    privData->significanceLevel = *((double*)nativeValue);
                    STEER_FreeMemory(&nativeValue);
                }
                if (result == STEER_RESULT_SUCCESS)
                {
                    if (parameters->parameter[i].precision != NULL)
                        result = STEER_ConvertStringToUnsigned32BitInteger(
                            parameters->parameter[i].precision,
                            &(privData->significanceLevelPrecision));
                }
            }
            if (result != STEER_RESULT_SUCCESS) break;
        }

        if ((privData->bitstreamCount < MINIMUM_BITSTREAM_COUNT) ||
            (privData->bitstreamLength < MINIMUM_BITSTREAM_LENGTH) ||
            ((privData->bitstreamLength % 8) != 0) ||
            (privData->significanceLevel <= MINIMUM_SIGNIFICANCE_LEVEL) ||
            (privData->significanceLevel >= MAXIMUM_SIGNIFICANCE_LEVEL))
        {
            result = STEER_CHECK_ERROR(EINVAL);
        }

        if (result == STEER_RESULT_SUCCESS)
        {
            result = STEER_GetMinimumTestCount(privData->significanceLevel,
                                               privData->bitstreamCount,
                                               &(privData->minimumTestCountRequiredForSignificance),
                                               &(privData->predictedPassedTestCount),
                                               &(privData->predictedFailedTestCount));
        }

        if (result == STEER_RESULT_SUCCESS)
        {
            privData->configurationState[0].configurationId = 0;
            *testPrivateData = (void*)privData;
            *bufferSizeInBytes = privData->bitstreamLength / 8;
        }
    }

    if (result != STEER_RESULT_SUCCESS)
        STEER_FreeMemory((void**)&privData);
    return result;
}

// =================================================================================================
//  GetConfigurationCount
// =================================================================================================
uint32_t GetConfigurationCount(void* testPrivateData)
{
    return CONFIGURATION_COUNT;
}

// =================================================================================================
//  SetReport
// =================================================================================================
int32_t SetReport(void* testPrivateData, tSTEER_ReportPtr report)
{
    ((tDiehard_SqueezePrivateData*)testPrivateData)->report = report;
    return STEER_RESULT_SUCCESS;
}

// =================================================================================================
//  ExecuteTest
// =================================================================================================
int32_t ExecuteTest(void* testPrivateData,
                    const char* bitstreamId,
                    uint8_t* buffer,
                    uint64_t bufferSizeInBytes,
                    uint64_t bytesInBuffer,
                    uint64_t numZeros,
                    uint64_t numOnes)
{
    int32_t result = STEER_RESULT_SUCCESS;
    tDiehard_SqueezePrivateData* privData = (tDiehard_SqueezePrivateData*)testPrivateData;
    bool passed = false;
    char calculationStr[STEER_STRING_MAX_LENGTH] = { 0 };
    char criterionStr[STEER_STRING_MAX_LENGTH] = { 0 };
    uint64_t testId = 0;
    char* end = NULL;

    testId = strtoull(bitstreamId, &end, 0) - 1;

    privData->ones = numOnes;
    privData->zeros = numZeros;
    privData->configurationState[0].accumulatedOnes += numOnes;
    privData->configurationState[0].accumulatedZeros += numZeros;

    result = RunTest(privData, buffer, &passed);

    // Add calculations
    if (result == STEER_RESULT_SUCCESS)
    {
        memset(calculationStr, 0, STEER_STRING_MAX_LENGTH);
        sprintf(calculationStr, "%" PRIu64 "", numOnes);
        result = STEER_AddCalculationToTest(privData->report, 0, testId,
                                            STEER_JSON_TAG_ONES,
                                            STEER_JSON_VALUE_UNSIGNED_64_BIT_INTEGER,
                                            NULL, STEER_JSON_VALUE_BITS, calculationStr);
    }

    if (result == STEER_RESULT_SUCCESS)
    {
        memset(calculationStr, 0, STEER_STRING_MAX_LENGTH);
        sprintf(calculationStr, "%" PRIu64 "", numZeros);
        result = STEER_AddCalculationToTest(privData->report, 0, testId,
                                            STEER_JSON_TAG_ZEROS,
                                            STEER_JSON_VALUE_UNSIGNED_64_BIT_INTEGER,
                                            NULL, STEER_JSON_VALUE_BITS, calculationStr);
    }

    if (result == STEER_RESULT_SUCCESS)
    {
        memset(calculationStr, 0, STEER_STRING_MAX_LENGTH);
        sprintf(calculationStr, "%d", privData->numTrials);
        result = STEER_AddCalculationToTest(privData->report, 0, testId,
                                            "number of trials",
                                            STEER_JSON_VALUE_SIGNED_32_BIT_INTEGER,
                                            NULL, NULL, calculationStr);
    }

    if (result == STEER_RESULT_SUCCESS)
    {
        memset(calculationStr, 0, STEER_STRING_MAX_LENGTH);
        sprintf(calculationStr, STEER_DEFAULT_FLOATING_POINT_STRING_FORMAT,
                STEER_DEFAULT_FLOATING_POINT_PRECISION, privData->chiSquared);
        result = STEER_AddCalculationToTest(privData->report, 0, testId,
                                            "chi squared",
                                            STEER_JSON_VALUE_DOUBLE_PRECISION_FLOATING_POINT,
                                            STEER_JSON_VALUE_DEFAULT_FLOATING_POINT_PRECISION,
                                            NULL, calculationStr);
    }

    if (result == STEER_RESULT_SUCCESS)
    {
        memset(calculationStr, 0, STEER_STRING_MAX_LENGTH);
        sprintf(calculationStr, STEER_DEFAULT_FLOATING_POINT_STRING_FORMAT,
                STEER_DEFAULT_FLOATING_POINT_PRECISION, privData->probabilityValue);
        result = STEER_AddCalculationToTest(privData->report, 0, testId,
                                            STEER_JSON_TAG_PROBABILITY_VALUE,
                                            STEER_JSON_VALUE_DOUBLE_PRECISION_FLOATING_POINT,
                                            STEER_JSON_VALUE_DEFAULT_FLOATING_POINT_PRECISION,
                                            NULL, calculationStr);
    }

    // Add criteria
    if (result == STEER_RESULT_SUCCESS)
    {
        memset(criterionStr, 0, STEER_STRING_MAX_LENGTH);
        sprintf(criterionStr, "%s of %.*f >= %s of %.*f",
                STEER_JSON_TAG_PROBABILITY_VALUE,
                STEER_DEFAULT_FLOATING_POINT_PRECISION,
                privData->probabilityValue,
                STEER_JSON_TAG_SIGNIFICANCE_LEVEL,
                privData->significanceLevelPrecision,
                privData->significanceLevel);
        result = STEER_AddCriterionToTest(privData->report, 0, testId, criterionStr,
                                          (privData->probabilityValue >= privData->significanceLevel));
    }

    // Add evaluation
    if (result == STEER_RESULT_SUCCESS)
    {
        bool eval_passed = false;
        result = STEER_AddEvaluationToTest(privData->report, 0, testId, &eval_passed);
        if (result == STEER_RESULT_SUCCESS)
        {
            privData->configurationState[0].testsRun++;
            if (eval_passed)
                privData->configurationState[0].testsPassed++;
            else
                privData->configurationState[0].testsFailed++;
        }
    }

    STEER_FreeMemory((void**)&buffer);
    return result;
}

// =================================================================================================
//  FinalizeTest
// =================================================================================================
int32_t FinalizeTest(void** testPrivateData, uint64_t suppliedNumberOfBitstreams)
{
    int32_t result = STEER_RESULT_SUCCESS;
    tDiehard_SqueezePrivateData* privData = (tDiehard_SqueezePrivateData*)(*testPrivateData);

    if (privData != NULL)
    {
        double probabilityValueUniformity = 0.0;
        uint64_t proportionThresholdMinimum = 0;
        uint64_t proportionThresholdMaximum = 0;

        result = STEER_NistStsAddRequiredMetricsToConfiguration(privData->report, 0,
                    suppliedNumberOfBitstreams,
                    privData->minimumTestCountRequiredForSignificance,
                    privData->configurationState[0].testsPassed,
                    privData->predictedPassedTestCount,
                    privData->configurationState[0].accumulatedOnes,
                    privData->configurationState[0].accumulatedZeros);

        if (result == STEER_RESULT_SUCCESS)
        {
            result = STEER_NistStsAddMetricsToConfiguration(privData->report, 0, false,
                        suppliedNumberOfBitstreams, privData->significanceLevel,
                        &probabilityValueUniformity,
                        &proportionThresholdMinimum, &proportionThresholdMaximum);
        }

        if (result == STEER_RESULT_SUCCESS)
        {
            result = STEER_AddConfusionMatrixMetricsToConfiguration(privData->report, 0,
                        privData->minimumTestCountRequiredForSignificance,
                        privData->configurationState[0].testsRun,
                        privData->configurationState[0].testsPassed,
                        privData->configurationState[0].testsFailed,
                        privData->predictedPassedTestCount,
                        privData->predictedFailedTestCount);
        }

        if (result == STEER_RESULT_SUCCESS)
        {
            result = STEER_NistStsAddRequiredCriterionToConfiguration(privData->report, 0,
                        suppliedNumberOfBitstreams,
                        privData->configurationState[0].testsPassed,
                        privData->significanceLevel,
                        privData->significanceLevelPrecision,
                        privData->minimumTestCountRequiredForSignificance);
        }

        if (result == STEER_RESULT_SUCCESS)
        {
            result = STEER_NistStsAddCriteriaToConfiguration(privData->report, 0,
                        probabilityValueUniformity,
                        proportionThresholdMinimum, proportionThresholdMaximum,
                        privData->configurationState[0].testsRun,
                        privData->configurationState[0].testsPassed);
        }

        if (result == STEER_RESULT_SUCCESS)
            result = STEER_AddEvaluationToConfiguration(privData->report, 0);

        STEER_FreeMemory((void**)testPrivateData);
    }
    return result;
}

// =================================================================================================
//  main
// =================================================================================================
int main(int argc, const char* argv[])
{
    return STEER_Run(PROGRAM_NAME, argc, argv,
                     GetTestInfo, GetParametersInfo,
                     InitTest, GetConfigurationCount,
                     SetReport, ExecuteTest, FinalizeTest);
}

// =================================================================================================
